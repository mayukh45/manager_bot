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
                await collection.insert_one({'id': user.id, 'name': user.name,
                                             'data': {}, 'transactions': [], 'unverified': [],
                                             'unapproved': []})

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
            await collection.update_one({'id': member.id}, {'$push': {'unapproved': {"Mid": message.id, "message": message.clean_content, "left": len(paid_for)}}})
            await self.add_transaction(collection=collection, message=message, user=member, flag=False)

        '''Adding transaction in payee's collection'''
        await self.add_transaction(collection=collection, message=message, user=payee, flag=True)

    async def verify(self, payee, paid_for, guild_id, amount, message_id):
        """Adds a payment to DB"""

        collection = self.db[str(guild_id)]

        payee_doc = await collection.find_one({'id': payee.id})
        paid_for_doc = await collection.find_one({'id': paid_for.id})
        values = payee_doc['data']
        paid_for_values = paid_for_doc['data']
        if not self.unapproved(paid_for_doc, message_id):
            return

        if list(values.keys()).count(str(paid_for.id)) > 0:
            values[str(paid_for.id)] = values[str(paid_for.id)] + amount
        else:
            values[str(paid_for.id)] = amount

        '''Adding payment in paid_for's collection'''

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

        """Removing unapproved from paid_for's DB"""
        unapproved = paid_for_doc['unapproved']
        approved = None
        for message in unapproved:
            if message['Mid'] == message_id:
                approved = message
                break

        unapproved.remove(approved)
        await collection.update_one({'id': paid_for.id}, {'$set': {'unapproved': unapproved}})

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

    def unapproved(self, paid_for_doc, message_id):
        """Returns the unverified transactions of the user """
        unapproved = paid_for_doc['unapproved']
        for message in unapproved:
            if message['Mid'] == message_id:
                return True

        return False

    async def get_unapproved(self, guild_id, user):
        """Returns unapproved transactions of a user from DB"""
        doc = await self.db[str(guild_id)].find_one({'id': user.id})
        if doc is None or len(doc['unapproved']) == 0:
            return -1
        else:
            return doc['unapproved']

    async def add_self(self, user, amount, message):
        """Adds the amount on your own expenditure"""
        collection = self.db['personal_data']
        doc = await collection.find_one({'id': user.id})
        if doc is None:
            await collection.insert_one({'id': user.id, 'name': user.name, 'expenses': amount, 'personal_exp': []})
        else:
            data = doc['expenses']
            await collection.update_one({'id': user.id}, {'$set': {'expenses': data + amount}})
            if len(doc['personal_exp']) >= 20:
                await collection.update_one({'id': user.id}, {'$pop': {'personal_exp': -1}})

            await collection.update_one({'id': user.id}, {'$push': {'personal_exp': message.content[5:]}})

    async def get_personal_data(self, user):
        collection = self.db['personal_data']
        doc = await collection.find_one({'id': user.id})
        if doc is None:
            return -1

        personal_trans = []

        for transactions in doc['personal_exp']:
            personal_trans.append(transactions)

        personal_exp = doc['expenses']

        all_data = [personal_trans, personal_exp]
        return all_data






