from flask import Flask, render_template, request, redirect, jsonify, url_for, flash
from sqlalchemy import create_engine, asc
from sqlalchemy.orm import sessionmaker
from database_setup import Base, User, Category, Item

from flask import session as login_session
import random
import string

from oauth2client.client import flow_from_clientsecrets
from oauth2client.client import FlowExchangeError
import httplib2
import json
from flask import make_response
import requests

from functools import wraps

app = Flask(__name__)

CLIENT_ID = json.loads(
	open('client_secrets.json', 'r').read())['web']['client_id']
APPLICATION_NAME = 'Catalog Application'

# Connect to Database and create database session
engine = create_engine('sqlite:///catalog.db')
Base.metadata.bind = engine

DBSession = sessionmaker(bind=engine)
session = DBSession()

def login_required(f):
	@wraps(f)
	def decorated_function(*args, **kwargs):
		if 'username' in login_session:
			return f(*args, **kwargs)
		else:
			return redirect(url_for('mainPage', next=request.url))
	return decorated_function

@app.route('/gconnect', methods=['POST'])
def gconnect():
	# Validate state token
	if request.args.get('state') != login_session['state']:
		reponse = make_response(json.dumps('Invalid state paramater.'), 401)
		response.headers['Content-Type'] = 'application/json'
		return response

	# Obtain authorization code
	code = request.data

	try:
		# Upgrade the authorization code into a credentials object
		oauth_flow = flow_from_clientsecrets('client_secrets.json', scope='')
		oauth_flow.redirect_uri = 'postmessage'
		credentials = oauth_flow.step2_exchange(code)
	except FlowExchangeError:
		response = make_response(
			json.dumps('Failed to upgrade the authorization code.'), 401)
		reponse.headers['Content-Type'] = 'application/json'
		return response

	# Check that the access token is valid.
	access_token = credentials.access_token
	url = ('https://www.googleapis.com/oauth2/v1/tokeninfo?access_token=%s' % access_token)
	h = httplib2.Http()
	result = json.loads(h.request(url, 'GET')[1])
	# If there was an error in the access token info, abort.
	if result.get('error') is not None:
		response = make_response(json.dumps(result.get('error')), 500)
		response.headers['Content-Type'] = 'application/json'

	# Verify that the access token is used for the intended user.
	gplus_id = credentials.id_token['sub']
	if result['user_id'] != gplus_id:
		response = make_response(
			json.dumps("Token's user ID doesn't match given user ID."), 401)
		reponse.headers['Content-Type'] = 'application/json'
		return response

	# Verify that the access token is valid for this app.
	if result['issued_to'] != CLIENT_ID:
		response = make_response(
			json.dumps("Token's client ID does not match app's."), 401)
		print "Token's client ID does not match app's."
		response.headers['Content-Type'] = 'application/json'
		return response

	stored_credentials = login_session.get('credentials')
	stored_gplus_id = login_session.get('gplus_id')
	if stored_credentials is not None and gplus_id == stored_gplus_id:
		response = make_response(json.dumps('Current user is already connected.'), 200)
		response.headers['Content-Type'] = 'application/json'
		return response

	# Store the access token in the session for later use.
	login_session['access_token'] = credentials.access_token
	login_session['gplus_id'] = gplus_id

	# Get user info
	userinfo_url = 'https://www.googleapis.com/oauth2/v1/userinfo'
	params = {'access_token': credentials.access_token, 'alt': 'json'}
	answer = requests.get(userinfo_url, params = params)

	data = answer.json()

	login_session['username'] = data['name']
	login_session['picture'] = data['picture']
	login_session['email'] = data['email']

	# See if user exists, if not, make a new User
	user_id = getUserID(login_session['email'])
	if not user_id:
		user_id = createUser(login_session)
	login_session['user_id'] = user_id

	return redirect(url_for('mainPage'))

#DISCONNECT - Revoke a current user's token and reset their login_session.
@app.route('/gdisconnect/')
def gdisconnect():
	access_token = login_session['access_token']
	print "In gdisconnect access token is %s" % access_token
	print 'User name is: '
	print login_session['username']
	if access_token is None:
		print 'Access token is None.'
		response = make_response(
			json.dumps('Current user is not connected.'), 401)
		response.headers['Content-Type'] = 'application/json'
		return response
	url = 'https://accounts.google.com/o/oauth2/revoke?token=%s' % access_token
	h = httplib2.Http()
	result = h.request(url, 'GET')[0]
	print 'Result is'
	print result
	if result['status'] == '200':
		del login_session['access_token']
		del login_session['gplus_id']
		del login_session['username']
		del login_session['email']
		del login_session['picture']
		response = make_response(
			json.dumps('Successfully disconnected.'), 200)
		response.headers['Content-Type'] = 'application/json'
		print response
		return redirect(url_for('mainPage'))
	else:
		response = make_response(
			json.dumps('Failed to revoke token for given user'), 400)
		response.headers['Content-Type'] = 'application/json'
		return response

# JSON API to view all Categories
@app.route('/catalog/categories/JSON/')
def categoriesJSON():
	categories = session.query(Category).all()
	return jsonify(categories=[c.serialize for c in categories])

# JSON API to view all Items
@app.route('/catalog/items/JSON/')
def itemsJSON():
	items = session.query(Item).all()
	return jsonify(items=[i.serialize for i in items])

# JSON API to view all Items in a Category
@app.route('/catalog/<int:category_id>/JSON/')
def itemsInCategoryJSON(category_id):
	items = session.query(Item).filter_by(category_id = category_id).all()
	return jsonify(items=[i.serialize for i in items])

# Main page that lists all of the categories
@app.route('/')
@app.route('/catalog/')
def mainPage():
	# Create a state token to prevent request forgery.
	# Store it in the session for later validation.
	state = ''.join(random.choice(string.ascii_uppercase + string.digits) for x in xrange(32))
	login_session['state'] = state

	categories = session.query(Category).all()
	
	if 'username' not in login_session:
		return render_template('publicmain.html', categories = categories, STATE = state)
	else:
		username = login_session['username']
		return render_template('main.html', categories = categories, username = username)


# Page for a user to add a new category
@app.route('/catalog/new/', methods=['GET', 'POST'])
@login_required
def newCategory():
	if request.method == 'POST':
		newCategory = Category(
			name = request.form['name'],
			picture = request.form['picture'],
			user_id = login_session['user_id'])
		session.add(newCategory)
		session.commit()
		return redirect(url_for('mainPage'))
	else:
		return render_template('newcategory.html')

# Page for a user to edit an existing category
@app.route('/catalog/<int:category_id>/edit/', methods = ['GET', 'POST'])
@login_required
def editCategory(category_id):
	editedCategory = session.query(Category).filter_by(id = category_id).one()
	current_user_id = getUserID(login_session['email'])
	creator_user_id = editedCategory.user_id
	
	if request.method == 'POST':
		if request.form['name']:
			editedCategory.name = request.form['name']
		if request.form['picture']:
			editedCategory.picture = request.form['picture']
		session.add(editedCategory)
		session.commit()
		return redirect(url_for('categoryPage', category_id = category_id))
	else:
		if current_user_id == creator_user_id:
			return render_template('editcategory.html', category = editedCategory)
		else:
			return redirect(url_for('categoryPage', category_id = category_id))

# Page for a user to delete an existing category
@app.route('/catalog/<int:category_id>/delete/', methods = ['GET', 'POST'])
@login_required
def deleteCategory(category_id):
	deletedCategory = session.query(Category).filter_by(id = category_id).one()
	current_user_id = getUserID(login_session['email'])
	creator_user_id = deletedCategory.user_id
	
	if request.method == 'POST':
		session.delete(deletedCategory)
		session.commit()
		return redirect(url_for('mainPage'))
	else:
		if current_user_id == creator_user_id:
			return render_template('deletecategory.html', category = deletedCategory)
		else:
			return redirect(url_for('categoryPage', category_id = category_id))

# Page to show all of the items in a category
@app.route('/catalog/<int:category_id>/')
def categoryPage(category_id):
	category = session.query(Category).filter_by(id = category_id).one()
	items = session.query(Item).filter_by(category_id = category_id).all()
	creator = getUserInfo(category.user_id)
	if 'username' not in login_session:
		return render_template('publiccategorypage.html', items = items, category = category)
	else:
		return render_template('categorypage.html', items = items, category = category)


# Page for a user to add a new item to an existing category
@app.route('/catalog/<int:category_id>/new/', methods = ['GET', 'POST'])
@login_required
def newItem(category_id):
	if request.method == 'POST':
		newItem = Item(
			name = request.form['name'],
			description = request.form['description'],
			picture = request.form['picture'],
			category_id = category_id,
			user_id = login_session['user_id']
			)
		session.add(newItem)
		session.commit()
		return redirect(url_for('categoryPage', category_id = category_id))

	else:
		return render_template('newitem.html', category_id = category_id)

# Page that shows a specific item
@app.route('/catalog/<int:category_id>/<int:item_id>/')
def itemPage(category_id, item_id):
	item = session.query(Item).filter_by(id = item_id).one()
	creator = getUserInfo(item.user_id)
	if 'username' not in login_session:
		return render_template('publicitempage.html', item = item)
	else:
		return render_template('itempage.html', item = item)


# Page for a user to edit an existing item in an existing category
@app.route('/catalog/<int:category_id>/<int:item_id>/edit/', methods = ['GET', 'POST'])
@login_required
def editItem(category_id, item_id):
	editedItem = session.query(Item).filter_by(id = item_id).one()
	current_user_id = getUserID(login_session['email'])
	creator_user_id = editedItem.user_id

	if request.method == 'POST':
		if request.form['name']:
			editedItem.name = request.form['name']
		if request.form['description']:
			editedItem.description = request.form['description']
		if request.form['picture']:
			editedItem.picture = request.form['picture']
		session.add(editedItem)
		session.commit()
		return redirect(url_for('itemPage', category_id = category_id, item_id = item_id))
	else:
		if current_user_id == creator_user_id:
			return render_template('edititem.html', item = editedItem)
		else:
			return redirect(url_for('itemPage', category_id = category_id, item_id = item_id))

# Page for a user to delete an existing item in an existing category
@app.route('/catalog/<int:category_id>/<int:item_id>/delete/', methods = ['GET', 'POST'])
@login_required
def deleteItem(category_id, item_id):
	deletedItem = session.query(Item).filter_by(id = item_id).one()
	current_user_id = getUserID(login_session['email'])
	creator_user_id = deletedItem.user_id

	if request.method == 'POST':
		session.delete(deletedItem)
		session.commit()
		return redirect(url_for('categoryPage', category_id = category_id))
	else:
		if current_user_id == creator_user_id:
			return render_template('deleteitem.html', item = deletedItem)
		else:
			return redirect(url_for('itemPage', category_id = category_id, item_id = item_id))


def getUserID(email):
	try:
		user = session.query(User).filter_by(email = email).one()
		return user.id
	except:
		return None

def getUserInfo(user_id):
	user = session.query(User).filter_by(id = user_id).one()
	return user

def createUser(login_session):
	newUser = User(
		name = login_session['username'],
		email = login_session['email'],
		picture = login_session['picture']
	)
	session.add(newUser)
	session.commit()

	user = session.query(User).filter_by(email = login_session['email']).one()
	return user.id



if __name__ == '__main__':
    app.secret_key = 'super_secret_key'
    app.debug = True
    app.run(host='0.0.0.0', port=5000)