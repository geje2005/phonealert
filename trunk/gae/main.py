#!/usr/bin/env python

import datetime

import wsgiref.handlers


from google.appengine.ext import webapp
from google.appengine.ext import db

import twilio

gTwilioSid = 'SID'
gTwilioToken = 'TOKEN'
gPhoneNumber = 'CALLERID'
gAppHost = 'APPID.appspot.com'

class Message(db.Model):
	created = db.DateTimeProperty(auto_now_add=True)
	updated = db.DateTimeProperty( auto_now=True)
	state = db.StringProperty(default='active')
	number = db.PhoneNumberProperty()
	message = db.StringProperty()
	trys = db.IntegerProperty(default=0)

	def StartCall(self):
		account = twilio.Account(gTwilioSid, gTwilioToken)
		d = {
				'Caller':		gPhoneNumber,
				'Called':		self.number,
				'Url':			'http://%s/answered/%s'%(gAppHost, self.key()),
				'Method':		'GET'
		}
		account.request('/2008-08-01/Accounts/%s/Calls' % (gTwilioSid), 'POST', d)
		self.trys+=1
		self.put()


# Main page
class Main(webapp.RequestHandler):
	def post(self):
		if self.request.get('action') == 'Clear':
			for m in Message.all():
				m.delete()
		self.get()

	def get(self):
		self.response.out.write("""
			<html>
				<head>
					<title>PhoneAlert</title>
				</head>
				<body>
					<form action="/alert" method="post">
						<input type="text" name="number" value="">
						<br>
						<textarea name="msg" rows="3" cols="60"></textarea>
						<br>
						<input type="submit" value="Alert!">
						<br>
					</form>""")
	
		self.response.out.write("<table border=1 cellspacing=0>")
		self.response.out.write("<tr><td><b>Date</b></td><td><b>State</b></td><td><b>Trys</b></td><td><b>Number</b></td><td><b>Message</b></td>")
		for m in Message.all().order('-created'):
			self.response.out.write("<tr><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td>"%(m.created.strftime('%m/%d/%Y %H:%M:%S'), m.state, m.trys, m.number, m.message) )

		self.response.out.write("</table>")
		self.response.out.write("</br>")
		self.response.out.write('<form action="/" method="post">')
		self.response.out.write('<input type="submit" name="action" value="Clear">')
		self.response.out.write('</form>')
		self.response.out.write("</body></html>")


# Generate an outbound alert
class Alert(webapp.RequestHandler):
	def get(self):
		self.post()

	def post(self):
		strNumber = self.request.get('number')
		strMsg = self.request.get('msg', 'Alert!')
		m = Message(number=strNumber, message=strMsg )
		m.put()
		m.StartCall()

		self.redirect('/')
		

class Answered(webapp.RequestHandler):
	def get(self):
		strKey = self.request.path.split('/')[2]
		m = Message.get( db.Key(encoded=strKey) )
		m.put()

		if self.request.get('DialStatus') in ('answered', 'answered-human'):
			self.response.headers['Content-Type'] = 'text/xml'
			self.response.out.write('<?xml version="1.0" encoding="UTF-8"?>')
			self.response.out.write("""
				<Response>
					<Gather action="/button/%s" method="GET" numDigits="1">
						<Say>%s</Say>
						<Say>Press 1 to acknowledge this message</Say>
					</Gather>
				</Response>"""%(strKey, m.message))


class Button(webapp.RequestHandler):
	def get(self):
		strKey = self.request.path.split('/')[2]
		m = Message.get( db.Key(encoded=strKey) )
		strDigits = self.request.get('Digits')
		if strDigits == '1':
			m.state = 'delivered'
			m.put()
		self.response.headers['Content-Type'] = 'text/xml'
		self.response.out.write('<?xml version="1.0" encoding="UTF-8"?>')
		self.response.out.write("""
			<Response>
				<Say>Thank you!</Say>
				<Hangup/>
			</Response>""")

class Cron(webapp.RequestHandler):
	def get(self):
		for m in Message.all().filter('state =', 'active' ).order('created'):
			if m.trys >= 3:
				m.state='dead'
				m.put()
			elif m.updated < datetime.datetime.now() - datetime.timedelta(minutes=1):
				self.response.out.write(m.message)
				m.StartCall()
				break

def main():
	
	aEndpoints = [
			('/',				Main),
			('/alert',			Alert),
			('/answered/.*',	Answered),
			('/button/.*',		Button),
			('/cron',			Cron),
		]


	application = webapp.WSGIApplication(aEndpoints, debug=True)

	wsgiref.handlers.CGIHandler().run(application)


if __name__ == '__main__':
	main()
