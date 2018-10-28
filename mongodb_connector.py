import motor.motor_asyncio


class MongoDBConnector:
    """Handles connection with a MongoDB database."""

    def __init__(self, srv_url, db_name, loop):
        self.client = motor.motor_asyncio.AsyncIOMotorClient(srv_url, io_loop=loop)
        self.db = self.client[db_name]

    async def update(self, member_ids, amount):
        pass

    async def create_guild(self, name, guild_id):
        """Adds a guild ID to DB"""
        await self.db[str(guild_id)].insert_one({'name': name})

    async def remove_guild(self, guild_id):
        """Removes a guild ID from DB"""
        await self.db[str(guild_id)].drop()

    async def add_user(self, user, collection):
        """Adds user to DB"""
        if await collection.find_one({'id': user.id}) is None:
            await collection.insert_one({'id': user.id, 'name': user.name})

    async def pay(self, guild_id, payee, paid_for, amount, message):
        """Handles required operations on DB after the paid coomand"""
        collection = self.db[str(guild_id)]
        
        await collection.update_one({'id': payee.id}, {'$push': {'unverified': {"message":message.content,"left":len(paid_for)}}})
        doc = await collection.find_one({'id':payee.id})
        if list(doc.keys()).count('data') == 0:
            await collection.update_one({'id': payee.id}, {'$set': {'data': {}}}, upsert=True)
        doc = await collection.find_one({'id':payee.id})

        values = doc['data']
        for member in paid_for:
            if list(values.keys()).count(str(member.id)) > 0:
                values[str(member.id)] = values[str(member.id)] + amount
            else:
                values[str(member.id)] = amount
        await collection.update_one({'id':payee.id}, {'$set': {'data': values}})

    async def get_unverified(self, user, guild_id):
        """Returns the unverified messages of a user"""
        print(user.name)
        s = await self.db[str(guild_id)].find_one({'id':user.id})
        return s['unverified']



