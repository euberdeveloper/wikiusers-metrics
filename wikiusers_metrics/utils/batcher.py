from pymongo import MongoClient


class Batcher:

    def __init_connection(self) -> None:
        self.connection = MongoClient()
        self.database = self.connection.get_database(self.database)
        self.collection = self.database.get_collection(f'{self.lang}wiki')


    def __init__(
        self,
        database: str,
        lang: str,
        batch_size: int,
        query_filter: dict = {},
        query_projector: dict = None
    ):
        self.database = database
        self.lang = lang
        self.batch_size = batch_size
        self.query_filter = query_filter
        self.query_projector = query_projector
        self.__init_connection()
        self.batch_index = 0

    def __iter__(self):
        return self

    def __next__(self):
        data = list(
            self.collection.find(self.query_filter, self.query_projector)
                .skip(self.batch_size * self.batch_index)
                .limit(self.batch_size)
        )

        if (data):
            self.batch_index += 1
            return data

        raise StopIteration
