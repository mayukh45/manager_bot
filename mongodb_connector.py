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

    async def add_users(self, users, collection):
        """Adds user to DB"""

        for user in users:
            if await collection.find_one({'id': user.id}) is None:
                await collection.insert_one({'id': user.id, 'name': user.name, 'data': {}, 'transactions': []})

    async def pay(self, guild_id, payee, paid_for, amount, message):
        """Handles required operations on DB after the paid command"""

        temp = [payee]
        collection = self.db[str(guild_id)]
        await self.add_users(users=paid_for + temp, collection=collection)
        await collection.update_one({'id': payee.id}, {'$push': {'unverified': {"message": message.clean_content,"left":len(paid_for)}}})
        payee_doc = await collection.find_one({'id': payee.id})

        values = payee_doc['data']
        for member in paid_for:

            if list(values.keys()).count(str(member.id)) > 0:
                values[str(member.id)] = values[str(member.id)] + amount
            else:
                values[str(member.id)] = amount

            '''Adding payment in paid_for members collection'''
            each_member_doc = await collection.find_one({'id': member.id})
            each_member_values = each_member_doc['data']
            if list(each_member_values.keys()).count(str(payee.id)) > 0:
                each_member_values[str(payee.id)] = values[str(payee.id)] - amount
            else:
                each_member_values[str(member.id)] = -amount

            await collection.update_one({'id': member.id}, {'$set': {'data': each_member_values}})
            await self.add_transaction(collection=collection, message=message, user=member)

        '''Adding payment in payee's collection'''
        await collection.update_one({'id': payee.id}, {'$set': {'data': values}})
        await self.add_transaction(collection=collection, message=message, user=payee)

    async def get_unverified(self, user, guild_id):
        """Returns the unverified messages of a user"""

        s = await self.db[str(guild_id)].find_one({'id': user.id})
        return s['unverified']

    async def add_transaction(self, collection, user, message):
        await collection.update_one({'id': user.id}, {'$push': {'transactions': {"message": message.clean_content}}})
