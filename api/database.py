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
        self.engine = create_engine(connString)
        self.db = scoped_session(sessionmaker(bind=self.engine))

    def add_device(self, name, type, ip_addr, description=""):
        """
        Add a Device, returns the new device's id.
        TODO: add support for additional columns.  Could just require
        name and device type (only two NOT NULL in database) to add a device.
        From API, call update device to add other optional fields. Should
        change that to iterate over dictionary values and have seperate update
        statments, should be okay since commands not run until .commit()
        Could use **kwargs to pass variable number of key,pair args.  Add this
        to both add_device and to update device.  Or call update_device from
        this function to avoid writing it out twice
        """
        result = self.db.execute("INSERT INTO devices \
                                (name, device_type, description, ip_addr) \
                                VALUES (:name, :type, :description, :ip_addr) \
                                 RETURNING id",
                                {'name': name, 'type': type,
                                'description': description, 'ip_addr':ip_addr})

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

    def update_device(self, id, values):
        """
        Update device id with values dictionary.
        """

        self.db.execute("UPDATE devices \
                        SET name = :name, device_type = :type, \
                        description = :description, ip_addr = :ip_addr \
                        WHERE id = :id",
                        {'name': values['name'], 'type': values['device_type'],
                        'description': values['description'],
                        'ip_addr': values['ip_addr'], 'id': id})
        self.db.commit()

    def delete_device(self, id):
        """
        Delete device id from that database
        """
        self.db.execute("DELETE FROM devices WHERE id = :id", {'id': id})
        self.db.commit()
