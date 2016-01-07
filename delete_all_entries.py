from flask import Flask, render_template, request, redirect, jsonify, url_for, flash
from sqlalchemy import create_engine, asc
from sqlalchemy.orm import sessionmaker
from database_setup import Base, User, Category, Item

# Connect to Database and create database session
engine = create_engine('sqlite:///catalog.db')
Base.metadata.bind = engine

DBSession = sessionmaker(bind=engine)
session = DBSession()

categories = session.query(Category).all()

for c in categories:
	session.delete(c)
	session.commit()

items = session.query(Item).all()

for i in items:
	session.delete(i)
	session.commit()

users = session.query(User).all()

for u in users:
	session.delete(u)
	session.commit()

print "Deletion completed."