In order to track email conversions, we add Analytics campaign
tracking parameters to each link in an email.


|Parameter      | Value                                        |
|---------------|----------------------------------------------|
|utm_medium     | `email`                                      |
|utm_campaign   | `monthly alert on <date>`                    |
|utm_source     | `[dashbord-alert|analysis-alert]`            |
|utm_content    | `<json encoded data used to generate email>` |
|clientId       | `<UUID identifying the user>`                |

The `clientId` is used in the Analytics tracker setup, and is used to
identify a device.  When it isn't specified (i.e. when users visit our
website for the first time), the (default) Google Analytics code
creates a random one; this is stored in a cookie for 2 years.

As the majority of our visitors will never have a user account, the
effect is that once returning visitors have signed up for email
alerts, they will then appear as new visitors in Analytics:

* First visit - you get a new, random, client id
* Return visit - recorded in Analytics as a return visit because the same client id
  is used (via a cookie)
* Sign up to alerts - you get a new client id based on your user id,
  so you'll be marked as a new visit again

Why use the user id as the client id? Because users are logged out of
the website when they close the browser, but we want the session to
continue to be tracked as if it were the same user.

Note that Analytics does support the separate notion of a `userId`,
but you have to turn it on specifically in Analytics.  At this stage,
treating clients/users as the same thing is good enough, though note
we are setting the `userId` variable when we set up the tracker.

Among
[other things](https://documentation.mailgun.com/user_manual.html#webhooks),
Mailgun additionally gives us the opportunity to track:

* Opens
* Deliveries
* Bounces
* Spam complaints
* Clicks

The webhooks are configured in Mailgun, and then handled in
[signals/handlers.py](./openprescribing/frontend/signals/handlers.py),
which submits the information to Google Analytics.
