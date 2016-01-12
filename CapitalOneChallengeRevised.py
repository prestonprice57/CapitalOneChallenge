

from instagram.client import InstagramAPI
import sys
import os
import re
from bokeh.plotting import figure
from bokeh.io import vplot, output_file, show
import indicoio
from numpy import pi
import math

# Define number of posts to be returned 
MAX_COUNT = 100

class InstaPost:

	# Initialize all variables that will be used in the class as well as api keys
	def __init__(self):
		self.positiveX = []
		self.positiveY = []
		self.positiveRadius = []
		self.neutralX = []
		self.neutralY = []
		self.neutralRadius = []
		self.negativeX = []
		self.negativeY = []
		self.negativeRadius = []
		self.numPosts = 0
		self.positivePosts = 0
		self.negativePosts = 0
		self.neutralPosts = 0
		self.imageSentiment = []
		self.imageSentimentAverage = {
			'fear': 0,
			'angry':0,
			'sad':0,
			'neutral':0,
			'surprise':0,
			'happy':0
		}
		self.captionSentimentAverage = {
			'positive': 0,
			'neutral': 0,
			'negative':0
		}
		# Initiates the secrets and tokens needed for the Instagram API
		self.client_id = 'bec82b4b69cc435998eb2c9f82212fb4'
		self.client_secret = '6f7cd017a78945afaffcd992840a8fe5'
		self.access_token = '1147536024.bec82b4.fb48b565d9ad4fe09f64f63d64d4f664'
		# Token for Indico API
		indicoio.config.api_key = '61cdd30af4bbdfe5a21b92689a872234'

	# Loops through all recent #CapitalOne posts
	def loadRecentPosts(self,recent_tags, api):

		for tag in recent_tags:
			#split the string returned to get users id
			temp, new_id = tag.id.split('_')
			user = api.user(new_id)

			#gets amount of posts user has made
			postCount = user.counts['media']
			#gets the amount of followers the user has
			followers = user.counts['followed_by']
			#gets the amount of people the user is following
			following = user.counts['follows']
			#gets the number of likes of the post
			likes = tag.like_count

			print 'Post Number:', self.numPosts
			print likes, 'likes'
			print "Users Number of Posts:", postCount
			print "Followers:", followers
			print "Following:", following

			# Checks each word in caption to see if it is positive, neutral or negative and
			# puts it into a list then calculates its radius based on number of followers
			if tag.caption is not None:
				print(tag.caption.text)
				sentiment = indicoio.sentiment_hq(tag.caption.text)
				if sentiment >= 0.66:
					self.positivePosts+=1
					self.positiveY.append(sentiment*100)
					self.positiveX.append(self.numPosts%(MAX_COUNT/3))
					self.positiveRadius = self.calculateRadius(self.positiveRadius,followers)
				elif sentiment >= 0.33:
					self.neutralPosts+=1
					self.neutralY.append(sentiment*100)
					self.neutralX.append(self.numPosts%(MAX_COUNT/3))
					self.neutralRadius = self.calculateRadius(self.neutralRadius,followers)
				else:
					self.negativePosts+=1
					self.negativeY.append(sentiment*100)
					self.negativeX.append(self.numPosts%(MAX_COUNT/3))
					self.negativeRadius = self.calculateRadius(self.negativeRadius,followers)
					
			#Use Indico API to calculate image sentiment
			imageUrl = tag.images['low_resolution'].url
			self.imageSentiment.append(indicoio.fer(imageUrl))

			print # separate each post with a new line
			self.numPosts+=1

	# Calculates the radius of a specific post based on the users amount of followers
	def calculateRadius(self,radius, followers):
		divisor = 10.0 # lower number for larger ranges
		for i in range(21):
			if followers < 2**i:
				radius.append((i-1)/divisor)
		if followers > 2**20:
				radius.append((i-1)/divisor)
		return radius

	# After all posts are loaded, this is called to calculate average sentiment for captions
	# and images
	def calculateCaptionAndImageSentimentAverage(self):
		# Calculate caption sentiment average
		self.captionSentimentAverage['positive'] = float(self.positivePosts)/self.numPosts
		self.captionSentimentAverage['neutral'] = float(self.neutralPosts)/self.numPosts
		self.captionSentimentAverage['negative'] = float(self.negativePosts)/self.numPosts

		# Calculate image sentiment average 
		for item in self.imageSentiment:
			self.imageSentimentAverage['fear'] += item['Fear']/len(self.imageSentiment)
			self.imageSentimentAverage['angry'] += item['Angry']/len(self.imageSentiment)
			self.imageSentimentAverage['sad'] += item['Sad']/len(self.imageSentiment)
			self.imageSentimentAverage['neutral'] += item['Neutral']/len(self.imageSentiment)
			self.imageSentimentAverage['surprise'] += item['Surprise']/len(self.imageSentiment)
			self.imageSentimentAverage['happy'] += item['Happy']/len(self.imageSentiment)

	# Runs program
	def run(self):
		# Instantiates an Instagram API object using the python-instagram library
		api = InstagramAPI(client_secret=self.client_secret,access_token=self.access_token) 

		# Get the recent #capitalone tags
		recent_tags, next = api.tag_recent_media(tag_name="CapitalOne", count=MAX_COUNT)
		nextCounter = math.ceil(MAX_COUNT/20.0)+1
		temp, max_tag = next.split("max_tag_id=")
		# Initialize variables to track number of positive, negative, and neutral posts
		# that load recent posts return
		positivePosts = 0
		negativePosts = 0
		neutralPosts = 0

		counter = 1
		while next and counter < nextCounter:
			# First run through the recent tags
			if counter == 1:
				self.loadRecentPosts(recent_tags,api)
			# Use pagination to run through more than 20 tags
			else:
				recent_tags, next = api.tag_recent_media(tag_name='CapitalOne', max_tag_id=max_tag)
				temp, max_tag = next.split('max_tag_id=')
				self.loadRecentPosts(recent_tags,api)
			counter+=1
		self.calculateCaptionAndImageSentimentAverage()
		self.makeGraphs()

	def makeGraphs(self):

		# create a new plot with a title and axis labels
		heat = figure(title="#CapitalOne Caption Sentiment Heat Map",  
			y_axis_label='Sentiment Percentage (%)', 
			y_range=(-5,105), x_range=(-5,(MAX_COUNT/3)+5))
		heat.axis[0].major_label_text_color = None
		heat.axis[0].ticker.num_minor_ticks = 0

		positiveColor = "#003A6F" # Capital One woodmark color
		neutralColor = "#686868" # Grey neutral color
		negativeColor = "#A12830" # Capital One logo color

		# Create different colored circles based on sentiment
		heat.circle(self.positiveX, self.positiveY, radius=self.positiveRadius, fill_color=positiveColor, fill_alpha=0.5, line_color=None)
		heat.circle(self.neutralX, self.neutralY, radius=self.neutralRadius, fill_color=neutralColor, fill_alpha=0.5, line_color=None)
		heat.circle(self.negativeX, self.negativeY, radius=self.negativeRadius, fill_color=negativeColor, fill_alpha=0.5, line_color=None)

		# Adds sentiment n to n-1 to create a list from 0-1
		captionAvgTemp = {
			'positive': self.captionSentimentAverage['positive'],
			'neutral': self.captionSentimentAverage['neutral']+self.captionSentimentAverage['positive'],
			'negative': self.captionSentimentAverage['negative']+self.captionSentimentAverage['neutral']+self.captionSentimentAverage['positive']
		}
		# Creates slices for pie graphs
		startsCaption = [captionAvgTemp[p]*2*pi for p in captionAvgTemp]
		startsCaption.insert(0,0)
		del startsCaption[-1]
		endsCaption = [captionAvgTemp[p]*2*pi for p in captionAvgTemp]
		colors1 = [positiveColor,neutralColor,negativeColor]
		legend1 = ["Positive", "Neutral", "Negative"]

		#create plot
		captionPie = figure(title="#CapitalOne Caption Sentiment Pie Graph",x_range=(-1,1.5), y_range=(-1,1))

		#create pie chart and legend
		captionPie.wedge(x=.2, y=0, radius=1, start_angle=startsCaption, end_angle=endsCaption, color=colors1)
		captionPie.circle(0,0,radius=0,legend=legend1[0],color=colors1[0])
		captionPie.circle(0,0,radius=0,legend=legend1[1],color=colors1[1])
		captionPie.circle(0,0,radius=0,legend=legend1[2],color=colors1[2])

		# Turn off tick labels
		captionPie.axis.major_label_text_color = None
		# Turn off tick marks
		captionPie.axis.major_tick_line_color = None
		captionPie.axis[0].ticker.num_minor_ticks = 0
		captionPie.axis[1].ticker.num_minor_ticks = 0

		# Each average adds the average before it so the array will be a list containing floats from 0-1
		# This is necessary to make the pie graph
		imageAvgTemp = self.imageSentimentAverage
		prevAvg = ""
		for avg in imageAvgTemp:
			if prevAvg != "":
				imageAvgTemp[avg] += imageAvgTemp[prevAvg]
			prevAvg = avg
		# Create slices for pie graph
		startsImage = [imageAvgTemp[p]*2*pi for p in imageAvgTemp]
		startsImage.insert(0,0)
		del startsImage[-1]
		endsImage = [imageAvgTemp[p]*2*pi for p in imageAvgTemp]

		# a color for each pie piece
		colors2 = ["#A12830", "#FAA43A", "#5DA5DA", "#686868", "#DECF3F", "#003A6F"]
		legend2 = ["Fear", "Angry", "Sad", "Neutral", "Surprise", "Happy"]

		#create plot
		imagePie = figure(title="#CapitalOne Image Sentiment Pie Graph",x_range=(-1,1.5), y_range=(-1,1))

		#create pie chart and legend
		imagePie.wedge(x=.2, y=0, radius=1, start_angle=startsImage, end_angle=endsImage, color=colors2)
		imagePie.circle(0,0,radius=0,legend=legend2[0],color=colors2[0])
		imagePie.circle(0,0,radius=0,legend=legend2[1],color=colors2[1])
		imagePie.circle(0,0,radius=0,legend=legend2[2],color=colors2[2])
		imagePie.circle(0,0,radius=0,legend=legend2[3],color=colors2[3])
		imagePie.circle(0,0,radius=0,legend=legend2[4],color=colors2[4])
		imagePie.circle(0,0,radius=0,legend=legend2[5],color=colors2[5])

		# Turn off tick labels
		imagePie.axis.major_label_text_color = None  
		# Turn off tick marks 
		imagePie.axis.major_tick_line_color = None
		imagePie.axis[0].ticker.num_minor_ticks = 0
		imagePie.axis[1].ticker.num_minor_ticks = 0

		# output to static HTML file
		output_file("sentimentgraphs.html", title="#CapitalOne Trend")
		p = vplot(heat,captionPie,imagePie)
		# show the results
		show(p)

insta = InstaPost()
insta.run()
print "Number of positive posts:", insta.positivePosts, "  Percentage: %.1f%%" % (insta.captionSentimentAverage['positive']*100)
print "Number of negative posts:", insta.negativePosts, "  Percentage: %.1f%%" % (insta.captionSentimentAverage['negative']*100)
print "Number of neutral posts: ", insta.neutralPosts,  "  Percentage: %.1f%%" % (insta.captionSentimentAverage['neutral']*100)
print "Total number of posts:   ", insta.numPosts

