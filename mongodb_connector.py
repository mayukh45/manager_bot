import motor.motor_asyncio


class MongoDBConnector:
    """Handles connection with a MongoDB database."""

    def __init__(self, srv_url, db_name, loop):
        self.client = motor.motor_asyncio.AsyncIOMotorClient(srv_url, io_loop=loop)
        self.db = self.client[db_name]

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
                await collection.insert_one({'id': user.id, 'name': user.name, 'data': {}, 'transactions': [], 'unverified': []})

    async def pay(self, guild_id, payee, paid_for, amount, message):
        """Handles required operations on DB after the paid command"""

        if amount == 0 or len(paid_for) == 0:
            return
        temp = [payee]
        collection = self.db[str(guild_id)]
        await self.add_users(users=paid_for + temp, collection=collection)
        await collection.update_one({'id': payee.id}, {'$push': {'unverified': {"Mid": message.id, "message": message.clean_content, "left": len(paid_for)}}})

        '''Adding transaction in paid_for members collection'''
        for member in paid_for:
            await self.add_transaction(collection=collection, message=message, user=member, flag=False)

        '''Adding transaction in payee's collection'''
        await self.add_transaction(collection=collection, message=message, user=payee, flag=True)

    async def verify(self, payee, paid_for, guild_id, amount, message_id):
        """Adds a payment to DB"""

        collection = self.db[str(guild_id)]
        payee_doc = await collection.find_one({'id': payee.id})
        values = payee_doc['data']
        if list(values.keys()).count(str(paid_for.id)) > 0:
            values[str(paid_for.id)] = values[str(paid_for.id)] + amount
        else:
            values[str(paid_for.id)] = amount

        '''Adding payment in paid_for's collection'''
        paid_for_doc = await collection.find_one({'id': paid_for.id})
        paid_for_values = paid_for_doc['data']
        if list(paid_for_values.keys()).count(str(payee.id)) > 0:
            paid_for_values[str(payee.id)] = paid_for_values[str(payee.id)] - amount
        else:
            paid_for_values[str(payee.id)] = - amount

        await collection.update_one({'id': paid_for.id}, {'$set': {'data': paid_for_values}})

        '''Adding payment in payee's collection'''
        await collection.update_one({'id': payee.id}, {'$set': {'data': values}})

        """Decreasing value of left verifications from DB"""
        unverified = payee_doc['unverified']
        verified = None
        for message in unverified:
            if message['Mid'] == message_id:
                verified = message
                break
        if verified['left'] == 1:
            unverified.remove(verified)
        else:
            verified['left'] -= 1

        await collection.update_one({'id': payee.id}, {'$set': {'unverified': unverified}})

    async def get_unverified(self, user, guild_id):
        """Returns the unverified messages of a user from DB"""

        doc = await self.db[str(guild_id)].find_one({'id': user.id})
        if doc is None or len(doc['unverified']) == 0:
            return -1
        else:
            return doc['unverified']

    async def add_transaction(self, collection, user, message, flag):
        """Adds a transaction detail to DB"""
        raw_message = message.clean_content
        raw_message = raw_message[raw_message.index(" "):]
        if flag:
            final_message = "You paid < " + raw_message + " >"
        else:
            final_message = message.author.name + " paid < " + raw_message + " >"

        doc = await collection.find_one({'id': user.id})
        if len(doc['transactions']) >= 10:
            await collection.update_one({'id': user.id}, {'$pop': {'transactions': -1}})

        await collection.update_one({'id': user.id}, {'$push': {'transactions': {"message": final_message}}})

    async def get_transactions(self, guild_id, user):
        """Returns transactions of a user from DB"""
        doc = await self.db[str(guild_id)].find_one({'id': user.id})
        if doc is None or len(doc['transactions']) == 0:
            return -1
        else:
            return doc['transactions']

    async def get_data(self, guild_id, user):
        """Returns current data of a user from DB"""
        doc = await self.db[str(guild_id)].find_one({'id': user.id})
        if doc is None or len(doc['data']) == 0:
            return -1
        else:
            return doc['data']




