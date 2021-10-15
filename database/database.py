from tinydb import TinyDB, Query
# from tinydb.storages import JSONStorage, Storage
# from tinydb.middlewares import CachingMiddleware


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
class DatabaseStorage:
    undirected = '{"_default": {}}'
    directed = '{"_default": {}}'
    command = '{"_default": {}}'

    @classmethod
    def load_data(cls):
        pass


class UndirectedDatabase:
    def __init__(self, database_path):
        self.db = TinyDB(database_path)
        # self.db = TinyDB(database_path, storage=MyMiddleware(JSONStorage))

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
        self.db = TinyDB(database_path)

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
        self.db = TinyDB(database_path)
        # self.db = TinyDB(database_path, storage=MyMiddleware(JSONStorage))

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
        self.db = TinyDB(database_path)
        # self.db = TinyDB(database_path, storage=MyMiddleware(JSONStorage))

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
