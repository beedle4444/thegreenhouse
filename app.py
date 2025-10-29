from the_greenhouse import create_app, db

app = create_app()

if __name__ == '__main__':
    with app.app_context():
        # Automatically create all tables
        db.create_all()
        print("Database tables created/verified successfully!")
    app.run()