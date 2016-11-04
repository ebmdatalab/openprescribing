In order to track email conversions, we add Analytics campaign
tracking parameters to each link in an email.


|Parameter      | Value                                        |
|---------------|----------------------------------------------|
|utm_medium     | `email`                                      |
|utm_campaign   | `monthly alert on <date>`                    |
|utm_source     | `[dashbord-alert|analysis-alert]`            |

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
