import json
import os
import io
from tinydb import TinyDB, Query
from tinydb.storages import Storage
from typing import Dict, Any, Optional


class MyJSONStorage(Storage):
    last_session_id = ""
    undir_inited = False
    dir_inited = False
    com_inited = False
    undir_db = ""
    dir_db = ""
    com_db = ""

    @classmethod
    def reset_state(cls):
        cls.undir_inited = False
        cls.dir_inited = False
        cls.com_inited = False
        cls.undir_db = ""
        cls.dir_db = ""
        cls.com_db = ""

    def __init__(self, path: str, create_dirs=False,
                 encoding=None, access_mode='r+', **kwargs):
        super().__init__()

        self._mode = access_mode
        self.kwargs = kwargs

        if "undirected" in path:
            self.handle_undir(path)
        elif "directed" in path:
            self.handle_dir(path)
        elif "command" in path:
            self.handle_com(path)

        # with open(path, "r") as f:
        #     data = json.load(f)
        #     MyJSONStorage.db = json.dumps(data)

        # # Open the file for reading/writing
        # # self._handle = open(path, mode=self._mode, encoding=encoding)
        # self._handle = io.StringIO(MyJSONStorage.db)

    def handle_undir(self, path):
        self.my_mode = 0
        if MyJSONStorage.undir_inited:
            self._handle = io.StringIO(MyJSONStorage.undir_db)
            return

        MyJSONStorage.undir_inited = True
        with open(path, "r") as f:
            data = json.load(f)
            MyJSONStorage.undir_db = json.dumps(data)

        # Open the file for reading/writing
        # self._handle = open(path, mode=self._mode, encoding=encoding)
        self._handle = io.StringIO(MyJSONStorage.undir_db)

    def handle_dir(self, path):
        self.my_mode = 1
        if MyJSONStorage.dir_inited:
            self._handle = io.StringIO(MyJSONStorage.dir_db)
            return

        MyJSONStorage.dir_inited = True
        with open(path, "r") as f:
            data = json.load(f)
            MyJSONStorage.dir_db = json.dumps(data)

        self._handle = io.StringIO(MyJSONStorage.dir_db)

    def handle_com(self, path):
        self.my_mode = 2
        if MyJSONStorage.com_inited:
            self._handle = io.StringIO(MyJSONStorage.com_db)
            return

        MyJSONStorage.com_inited = True
        with open(path, "r") as f:
            data = json.load(f)
            MyJSONStorage.com_db = json.dumps(data)

        self._handle = io.StringIO(MyJSONStorage.com_db)

    def close(self) -> None:
        self._handle.close()

    def read(self) -> Optional[Dict[str, Dict[str, Any]]]:
        # Get the file size by moving the cursor to the file end and reading
        # its location
        self._handle.seek(0, os.SEEK_END)
        size = self._handle.tell()

        if not size:
            # File is empty so we return ``None`` so TinyDB can properly
            # initialize the database
            return None
        else:
            # Return the cursor to the beginning of the file
            self._handle.seek(0)

            # Load the JSON contents of the file
            return json.load(self._handle)

    def write(self, data: Dict[str, Dict[str, Any]]):
        # Move the cursor to the beginning of the file just in case
        self._handle.seek(0)

        # Serialize the database state using the user-provided arguments
        serialized = json.dumps(data, **self.kwargs)

        # Write the serialized data to the file
        try:
            self._handle.write(serialized)
        except io.UnsupportedOperation:
            raise IOError('Cannot write to the database. Access mode is "{0}"'.format(self._mode))

        # Ensure the file has been writtens
        self._handle.flush()

        # Remove data that is behind the new cursor in case the file has
        # gotten shorter
        self._handle.truncate()

        # update the variable
        if self.my_mode == 0:
            MyJSONStorage.undir_db = self._handle.getvalue()
        elif self.my_mode == 1:
            MyJSONStorage.dir_db = self._handle.getvalue()
        elif self.my_mode == 2:
            MyJSONStorage.com_db = self._handle.getvalue()

# class MyMiddleware(CachingMiddleware):
#     def __init__(self, storage_cls):
#         # Initialize the parent constructor
#         super().__init__(storage_cls)

#     def flush(self):
#         """
#         Flush all unwritten data to disk.
#         """
#         # doing nothing
#         pass
# class DatabaseStorage:
#     undirected = '{"_default": {}}'
#     directed = '{"_default": {}}'
#     command = '{"_default": {}}'

#     @classmethod
#     def load_data(cls):
#         pass


class UndirectedDatabase:
    def __init__(self, database_path):
        # self.db = TinyDB(database_path)
        self.db = TinyDB(database_path, storage=MyJSONStorage)

    # change database
    def change_db(self, database_path):
        if '.json' not in database_path:
            return False

        self.db = TinyDB(database_path)
        return True

    def insert_or_update(self, name, feature, m_id=None):
        Gesture = Query()
        result = self.db.search(Gesture.name == name)
        # gesture already exist
        if len(result) > 0:
            self.db.update({'feature': feature},
                           Gesture.name == name)
        else:
            if m_id is None:
                print("Please provide an ID")
                return False
            self.db.insert({
                'id': m_id,
                'name': name,
                'feature': feature
            })
        return True

    def rename(self, m_id, new_name):
        Gesture = Query()
        result = self.db.search(Gesture.id == m_id)
        # gesture not found
        if len(result) == 0:
            return False

        self.db.update({'name': new_name},
                       Gesture.id == m_id)
        return True

    def delete(self, m_id):
        Gesture = Query()
        result = self.db.search(Gesture.id == m_id)
        # gesture not found
        if len(result) == 0:
            return False

        self.db.remove(Gesture.id == m_id)
        return True

    # sample ouput:
    # [{'name': 'minh', 'feat': [1, 2]}, {'name': 'anh', 'feat': [3, 2]}]
    def all(self):
        return self.db.all()


class DirectedDatabase:
    def __init__(self, database_path):
        # self.db = TinyDB(database_path)
        self.db = TinyDB(database_path, storage=MyJSONStorage)

    # change database
    def change_db(self, database_path):
        if '.json' not in database_path:
            return False

        self.db = TinyDB(database_path)
        return True

    def insert_or_update(self, name, feature, m_id=None, und_id=None):
        Gesture = Query()
        result = self.db.search(Gesture.name == name)
        # gesture already exist
        if len(result) > 0:
            self.db.update({'feature': feature},
                           Gesture.name == name)
        else:
            if m_id is None or und_id is None:
                print("Please provide an ID")
                return False
            self.db.insert({
                'id': m_id,
                'name': name,
                'feature': feature,
                'und_id': und_id
            })
        return True

    def get_directed_data(self, und_id):
        Gesture = Query()
        result = self.db.search(Gesture.und_id == und_id)
        return result

    def get(self, name):
        Gesture = Query()
        result = self.db.search(Gesture.name == name)
        return result

    def rename(self, m_id, new_name):
        Gesture = Query()
        result = self.db.search(Gesture.id == m_id)
        # gesture not found
        if len(result) == 0:
            return False

        self.db.update({'name': new_name},
                       Gesture.id == m_id)
        return True

    def delete(self, m_id):
        Gesture = Query()
        result = self.db.search(Gesture.id == m_id)
        # gesture not found
        if len(result) == 0:
            return False

        self.db.remove(Gesture.id == m_id)
        return True

    def all(self):
        return self.db.all()


class DynamicDatabase:
    def __init__(self, database_path):
        # self.db = TinyDB(database_path)
        self.db = TinyDB(database_path, storage=MyJSONStorage)

    # change database
    def change_db(self, database_path):
        if '.json' not in database_path:
            return False

        self.db = TinyDB(database_path)
        return True

    def insert_or_update(self, name, feature, m_id=None, start_id=None, end_id=None):
        Gesture = Query()
        result = self.db.search(Gesture.name == name)
        # gesture already exist
        if len(result) > 0:
            self.db.update({'feature': feature},
                           Gesture.name == name)
        else:
            if m_id is None:
                print("Please provide an ID")
                return False
            self.db.insert({
                'id': m_id,
                'name': name,
                'feature': feature,
                'start_id': start_id,
                'end_id': end_id
            })
        return True

    def rename(self, m_id, new_name):
        Gesture = Query()
        result = self.db.search(Gesture.id == m_id)
        # gesture not found
        if len(result) == 0:
            return False

        self.db.update({'name': new_name},
                       Gesture.id == m_id)
        return True

    def delete(self, m_id):
        Gesture = Query()
        result = self.db.search(Gesture.id == m_id)
        # gesture not found
        if len(result) == 0:
            return False

        self.db.remove(Gesture.id == m_id)
        return True

    def all(self):
        return self.db.all()

class MappingDatabase:
    def __init__(self, database_path):
        # self.db = TinyDB(database_path)
        self.db = TinyDB(database_path, storage=MyJSONStorage)

    # change database
    def change_db(self, database_path):
        if '.json' not in database_path:
            return False

        self.db = TinyDB(database_path)
        return True

    def insert(self, command, gesture):
        MyQuery = Query()
        result = self.db.search(MyQuery.command == command)
        # gesture already exist
        if len(result) == 0:
            self.db.insert({
                'command': command,
                'gesture': gesture
            })
            return True
        return False

    def update(self, command, gesture):
        MyQuery = Query()
        result = self.db.search(MyQuery.command == command)
        # gesture already exist
        if len(result) > 0:
            self.db.update({'gesture': gesture},
                           MyQuery.command == command)
            return True
        return False

    def delete(self, command):
        MyQuery = Query()
        result = self.db.search(MyQuery.command == command)
        # gesture not found
        if len(result) == 0:
            return False

        self.db.remove(MyQuery.command == command)
        return True

    def get_command(self, gesture):
        MyQuery = Query()
        result = self.db.search(MyQuery.gesture == gesture)
        if len(result) == 0:
            return None
        return result[0]['command']

    def all(self):
        return self.db.all()
