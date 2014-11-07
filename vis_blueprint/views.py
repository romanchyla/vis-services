from flask import current_app, Blueprint, jsonify, request
from flask.ext.restful import Resource, reqparse
from lib import word_cloud
from lib import author_network
import config


blueprint = Blueprint(
	'visualization',
	__name__,
	static_folder=None,
)

#function to help passing flask parameters to solr query
def ensure_int_variable(val, default):
	if val:
		return int(val)
	else:
		return default


class WordCloud(Resource):
  '''Returns collated tf/idf data for a solr query'''
  scopes = [] 

  def get(self):

  	parser = reqparse.RequestParser()
	parser.add_argument('q', type=str, required=True)
	parser.add_argument('fq', type=str)
	parser.add_argument('start', type=int)
	parser.add_argument('rows', type=int)
	parser.add_argument('min_percent_word', type=int)
	parser.add_argument('min_occurences_word', type=int)
	args = parser.parse_args()



	fq = args.get("fq", None)

	rows = args.get("rows", None)
	if not rows or rows > config.MAX_RECORDS:
		rows = config.MAX_RECORDS

	start = args.get("start", None)
	if not start:
		start = config.START

	min_percent_word = args.get("min_percent_word", None)
	if not min_percent_word:
		min_percent_word = config.MIN_PERCENT_WORD

	min_occurences_word = args.get("min_occurrences_word", None)
	if not min_occurrences_word:
		min_occurences_word = config.MIN_OCCURENCES_WORD

	d = {
		'q' : q,
		'fq' : fq,
		'rows': rows,
		'start': start,
		'facets': [], 
		'highlights': [],
		#fields parameter is necessary for tvrh query
		'fields': ['id'],
		'defType':'aqp', 
		'tv.tf_idf': 'true', 
		'tv.tf': 'true', 
		'tv.positions':'false',
		'tf.offsets':'false',
		'tv.fl':'abstract,title',
		'fl':'id,abstract,title',
		'wt': 'json',	
		 }

	response = current_app.client.session.get(config.TVRH_SOLR_PATH , params = d)
	
	if response.status_code == 200:
		data = response.json()
	else:
		return {"Error": "There was a connection error. Please try again later"}, response.status_code

	if data:
		word_cloud_json = word_cloud.generate_wordcloud(data, min_percent_word=min_percent_word, min_occurences_word=min_occurences_word)

	return word_cloud_json, 200

class AuthorNetwork(Resource):
  '''Returns author network data for a solr query'''
  scopes = [] 

  def get(self):

  	parser = reqparse.RequestParser()
	parser.add_argument('q', type=str, required=True)
	parser.add_argument('fq', type=str)
	parser.add_argument('start', type=int)
	parser.add_argument('rows', type=int)
	parser.add_argument('max_groups', type=int)
	args = parser.parse_args()

	#assign all query parameters and config variabls

	fq = args.get("fq", None)

	rows = args.get("rows", None)
	if not rows or rows > config.MAX_RECORDS:
		rows = config.MAX_RECORDS

	start = args.get("start", None)
	if not start:
		start = config.START

	max_groups = args.get("max_groups", None)
	if not max_groups:
		max_groups = config.MAX_GROUPS

	#request data from solr

	d = {
		'q' : q,
		'fq' : fq,
		'rows': rows,
		'start': start,
		'facets': [], 
		'fl': 'author_norm', 
		'highlights': [], 
		'wt' : 'json'
		}

	response = current_app.client.session.get(config.SOLR_PATH , params = d)
	if response.status_code == 200:
		data = response.json()
	else:
		return {"Error": "There was a connection error. Please try again later"}, response.status_code

	if data:
		#get_network_with_groups expects a list of normalized authors
		data = [d.get("author_norm", []) for d in data["response"]["docs"]]
		author_network_json = author_network.get_network_with_groups(data, max_groups)

		return author_network_json, 200




