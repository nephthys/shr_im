# Simple action to manage the repository

clean:
	find . -name '*.pyc' | xargs rm
	find . -name 'Thumbs.db' | xargs rm
