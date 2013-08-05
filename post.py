import praw
import settings

def post(postTitle, postBody):
    r = praw.Reddit(user_agent=settings.userAgent)
    r.login(settings.username, settings.password)
    r.submit(settings.subreddit, postTitle, text=postBody)
