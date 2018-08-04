# insta-cryptonews

Fun Experiment!

I created this Twilio/Flask app as an experiment to gauge how quickly I could push news on instagram.

Steps: 
1) Text number to begin the process and create a new class instance. 
2) Text number to return a title of a random news article related to cryptocurrency.
3) Text a number to return a random photo related to cryptocurrency.
4) When the news article or photo have been selected, text a number to perform some work on the backend and upload to Instagram.

For the photo:
For the work on the backend, Python is downloading the photo, resizing to a smaller image, adding the article's title and author to the image and saving the image.

For the caption:
To generate the caption, a query is made to AWS's Comprehend for keyword analysis of the article's description. Another API call is made to Bitly to create a bitly url to use in the caption. While instagram doesn't appear links to be clickable in the caption, having a shorter url might be easier to copy/paste/type in user's browser.

When both of these tasks are complete, the photo is pushed to instagram and a text is sent back as acknowledgement.

Disclaimer:
Just an experiment; nothing more. Off to the next one!

Demo:
<video src="DEMO.mp4" width="320" height="200" controls preload></video>
