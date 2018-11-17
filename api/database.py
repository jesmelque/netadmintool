#!/usr/local/bin/python3

from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker
from configparser import ConfigParser


class NetAdminToolDB:
    """
    Database interface
    """

    def __init__(self, configFile):
        config = ConfigParser()
        config.read(configFile)

        dbuser = config['DATABASE']['dbusername']
        dbpass = config['DATABASE']['dbpassword']
        dbhost = config['DATABASE']['hostname']
        dbport = config['DATABASE']['port']
        dbname = config['DATABASE']['dbname']

        connString = f"postgresql://{dbuser}:{dbpass}@{dbhost}:{dbport}/{dbname}"
        self.dbname = dbname
        self.engine = create_engine(connString)
        self.db = scoped_session(sessionmaker(bind=self.engine))

    def add_device(self, name, ip_addr, make, model,
        sw_version, serial_number, datacenter, location, console="",
        description="", notes=""):
        """
        Add a Device, returns the new device's id.
        """
        result = self.db.execute("INSERT INTO devices \
                                (name, ip_addr, make, model, \
                                sw_version, serial_number, datacenter, \
                                location, console, description, notes) \
                                VALUES (:name, :ip_addr, :make, \
                                :model, :ver, :serial_num, :datacenter, \
                                :loc, :con, :descr, :notes)  RETURNING id",
                                {'name': name, 'ip_addr': ip_addr, 'make': make,
                                'model': model, 'ver': sw_version,
                                'serial_num': serial_number,
                                'datacenter': datacenter, 'loc': location,
                                'con': console, 'descr': description,
                                'notes': notes})

        self.db.commit()

        return result.fetchone().id


    def get_device(self, id=0):
        """
        Returns a dictionary of device with id. If id is not provided,
        returns a list of dictionaries of all devices in database
        """
        if id != 0:
            device = self.db.execute("SELECT * FROM devices WHERE id = :id",
                                    {'id': id}).fetchone()
        else:
            device = self.db.execute("SELECT * FROM devices").fetchall()

        # Added Commit to avoid crash with error.
        # "QueuePool limit of size 5 overflow 10 reached, connection timed out,
        # timeout 30"
        # Is there a better way?  Just need to free connection , not commit
        # changes?
        self.db.commit()
        return device

    def get_device_name(self, name):
        """
        Returns first device with name
        """
        device = self.db.execute("SELECT * FROM devices WHERE name = :name",
                            {'name': name }).fetchone()

        # Add commit to avoid crash - see get_device(self,id=0) comments
        self.db.commit()
        return device

    def update_device(self, id, **updates):
        """
        Update device with id with named arguments
        """

        for key, value in updates.items():
            if key == 'name':
                self.db.execute('UPDATE devices SET name = :value \
                                WHERE id = :id',
                                {'value': value, 'id':id})
            if key == 'ip_addr':
                self.db.execute('UPDATE devices SET ip_addr = :value \
                                WHERE id = :id',
                                {'value': value, 'id':id})
            if key == 'make':
                self.db.execute('UPDATE devices SET make = :value \
                                WHERE id = :id',
                                {'value': value, 'id':id})
            if key == 'model':
                self.db.execute('UPDATE devices SET model = :value \
                                WHERE id = :id',
                                {'value': value, 'id':id})
            if key == 'sw_version':
                self.db.execute('UPDATE devices SET sw_version = :value \
                                WHERE id = :id',
                                {'value': value, 'id':id})
            if key == 'serial_number':
                self.db.execute('UPDATE devices SET serial_number = :value \
                                WHERE id = :id',
                                {'value': value, 'id':id})
            if key == 'datacenter':
                self.db.execute('UPDATE devices SET datacenter = :value \
                                WHERE id = :id',
                                {'value': value, 'id':id})
            if key == 'location':
                self.db.execute('UPDATE devices SET location = :value \
                                WHERE id = :id',
                                {'value': value, 'id':id})
            if key == 'console':
                self.db.execute('UPDATE devices SET console = :value \
                                WHERE id = :id',
                                {'value': value, 'id':id})
            if key == 'description':
                self.db.execute('UPDATE devices SET description = :value \
                                WHERE id = :id',
                                {'value': value, 'id':id})
            if key == 'notes':
                self.db.execute('UPDATE devices SET notes = :value \
                                WHERE id = :id',
                                {'value': value, 'id':id})

        self.db.commit()


    def delete_device(self, id):
        """
        Delete device with id from database
        """
        self.db.execute("DELETE FROM devices WHERE id = :id", {'id': id})
        self.db.commit()


    def create_tables(self):
        """
        Recreate database tables
        """

        self.db.execute('DROP TABLE IF EXISTS devices')
        self.db.execute('DROP TABLE IF EXISTS roles CASCADE')
        self.db.execute('DROP TABLE IF EXISTS users')


        self.db.execute('CREATE TABLE devices ( \
            id SERIAL PRIMARY KEY, \
            name VARCHAR NOT NULL, \
            ip_addr INET NOT NULL, \
            make VARCHAR NOT NULL, \
            model VARCHAR NOT NULL, \
            sw_version VARCHAR NOT NULL, \
            serial_number VARCHAR NOT NULL, \
            datacenter VARCHAR NOT NULL, \
            location VARCHAR NOT NULL, \
            console VARCHAR, \
            description VARCHAR, \
            notes VARCHAR)')

        self.db.execute('CREATE TABLE roles ( \
            id SERIAL PRIMARY KEY, \
            role_name VARCHAR NOT NULL UNIQUE)')

        self.db.execute('CREATE TABLE users ( \
            id SERIAL PRIMARY KEY, \
            username VARCHAR NOT NULL UNIQUE, \
            password VARCHAR NOT NULL, \
            display_name VARCHAR NOT NULL, \
            role_id INTEGER REFERENCES roles)')

        self.db.execute("INSERT INTO roles (role_name) VALUES ('admin')")
        self.db.execute("INSERT INTO roles (role_name) VALUES ('readonly')")

        self.db.commit()

    def get_role(self, role_id):
        """
        Returns a dictionary of role with role_id.
        """
        role = self.db.execute("SELECT * FROM roles WHERE id = :role_id",
            {'role_id': role_id}).fetchone()

        self.db.commit()
        return role

    def get_role_name(self, role_name):
        """
        Returns a dictionary of role with name
        """
        role = self.db.execute("SELECT * FROM roles WHERE role_name = :role_name",
            {'role_name': role_name}).fetchone()

        self.db.commit()
        return role


    def add_user(self, username, password, display_name, role_name):
        """
        Add a user, return's the new user's id
        """
        role = self.get_role_name(role_name)
        result = self.db.execute("INSERT INTO users (username, password, display_name, \
            role_id) VALUES (:username, :password, :display_name, :role_id) RETURNING id",
            {'username': username, 'password': password,
            'display_name': display_name, 'role_id': role.id})

        self.db.commit()

        return result.fetchone().id


    def get_user(self, user_id=0):
        """
        Return a dictionary of user with user_id. If id is not provided,
        returns a list of dictionaries of all users in database.
        Does not return password attribute
        """
        if user_id != 0:
            #user = self.db.execute("SELECT * FROM users WHERE id = :user_id",
            #    {'user_id': user_id}).fetchone()
            user = self.db.execute("SELECT users.id, username, display_name, role_name \
                FROM users JOIN roles ON users.role_id = roles.id \
                WHERE users.id = :user_id", {'user_id': user_id}).fetchone()
        else:
            #user = self.db.execute("SELECT * FROM users").fetchall()
            user = self.db.execute("SELECT users.id, username, display_name, role_name \
                FROM users JOIN roles ON users.role_id = roles.id").fetchall()

        self.db.commit()
        return user

    def get_user_name(self, username):
        """
        Return a dictionary of user with username.
        Does not return password attribute
        """
        #user = self.db.execute("SELECT * FROM users WHERE username = :username",
        #    {'username': username}).fetchone()
        user = self.db.execute("SELECT users.id, username, display_name, role_name \
            FROM users JOIN roles ON users.role_id = roles.id \
            WHERE users.username = :username", {'username': username}).fetchone()
        self.db.commit()
        return user

    def update_user(self, user_id, **updates):
        """
        Update user with id using named arguments
        """
        for key, value in updates.items():
            if key == 'username':
                self.db.execute("UPDATE users SET username = :value \
                                WHERE id = :id",
                                {'value': value, 'id': user_id})
            if key == 'password':
                self.db.execute("UPDATE users SET password = :value \
                                WHERE id = :id",
                                {'value': value, 'id': user_id})
            if key == 'display_name':
                self.db.execute("UPDATE users SET display_name = :value \
                                WHERE id = :id",
                                {'value': value, 'id': user_id})
            if key == 'role':
                role = self.get_role_name(value)
                if role != None:
                    self.db.execute("UPDATE users SET role_id = :value \
                                    WHERE id = :id",
                                    {'value': role.id, 'id': user_id})

        self.db.commit()

    def delete_user(self, user_id):
        """
        Delete user with user_id from database
        """
        self.db.execute("DELETE FROM users WHERE id = :id", {'id': user_id})
        self.db.commit()

    def authenticate_user(self, username, password):
        """
        Verify username and password
        """
        result = self.db.execute("SELECT id FROM users \
                WHERE username = :username AND password = :password",
                {'username': username, 'password': password}).fetchone()
        self.db.commit()
        if None == result:
            return False

        else:
            return True
