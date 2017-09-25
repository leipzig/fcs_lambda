attachment = """{{
    "attachments": [
        {{
            "fallback": "Required plain-text summary of the attachment.",
            "color": "#36a64f",
            "pretext": {pretext},
            "title": "Slack API Documentation",
            "title_link": "https://api.slack.com/",
            "text": "Optional text that appears within the attachment",
            "fields": [
                {{
                    "title": "Priority",
                    "value": "High",
                    "short": false
                }}
            ],
            "image_url": "http://my-website.com/path/to/image.jpg",
            "thumb_url": "http://example.com/path/to/thumb.png",
            "footer": "Slack API",
            "footer_icon": "https://platform.slack-edge.com/img/default_application_icon.png",
            "ts": 123456789
        }}
    ]
    }}
""".format(pretext="foo")