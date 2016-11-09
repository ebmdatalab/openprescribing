In order to track email conversions, we add Analytics campaign
tracking parameters to each link in an email.


|Parameter      | Value                                              |
|---------------|----------------------------------------------------|
|utm_medium     | `email`                                            |
|utm_campaign   | `monthly alert <date>`                             |
|utm_source     | `[dashbord-alert|analysis-alert]`                  |
|utm_content    | `/email/<utm_campaign>/<utm_source>/<bookmark_id>` |

Among
[other things](https://documentation.mailgun.com/user_manual.html#webhooks),
Mailgun additionally gives us the opportunity to track:

* Opens
* Deliveries
* Bounces
* Spam complaints
* Clicks
* Failed deliveries

The webhooks are configured in Mailgun, and then handled in
[signals/handlers.py](./openprescribing/frontend/signals/handlers.py),
which submits the information to Google Analytics.

All webhook events are recorded at debug level in the
`frontend.signals.handlers` log facility.  For the time being, these
are all logged to their own file in the production environment.
