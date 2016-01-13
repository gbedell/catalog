## Catalog Application

## Section 0: Introduction

The Catalog Application is a part of the Full Stack Web Developer Nanodegree at Udacity. 

This is a web application that stores category and item information created by users. Users can also edit and delete and data that they created.


## Section 1: Set Up Environment

To run this application, you must first connect to the supporting virtual machine. First, download and install Vagrant and VirtualBox.

Then, clone the fullstack-nanodegree-vm repository (https://github.com/udacity/fullstack-nanodegree-vm). 
For more information on setting that up, visit https://docs.google.com/document/d/1jFjlq_f-hJoAZP8dYuo5H3xY62kGyziQmiv9EPIA7tM/pub?embedded=true.


## Section 2: Requirements

This application requires several modules to successful execute. Install the following modules:
Flask == 0.9
SQLAlchemy == 0.8.4
oauth2client == 1.5.2
httplib2 == 0.9.1
requests == 2.7.0
google_api_python_client == 1.4.1


## Section 3: Installation

To clone the application repository, click the Fork button and clone to the vagrant folder in the repository you already cloned.


## Section 4: Setup

To setup the application, first navigate to the vagrant folder and type 'vagrant up' in the command line. This will launch the virtual machine.

Once that is complete, type 'vagrant ssh' to sign in to the virtual machine.

Once successful, to create the catalog.db database, type 'python database_setup.py' into the command line.


## Section 5: How to Run

To run the application, type 'python application.py' into the command line. To visit the application, go to http://localhost:5000 in your browser.


## Section 6: Usage

The two main features of the application are categories and items. Once on the home page, you can create a new category using the button at the bottom of the page.

Once a category is created, you can create items within that category by visiting that category's page and clicking to create a new item at the bottom of the page.

You can also edit and delete any categories or items that the user has created. You're not able to edit or delete items or categories that you didn't create.

You can also access JSON pages for category and item information. Simply navigate to that specific category or item page, and add '/JSON' to the end of the URL.