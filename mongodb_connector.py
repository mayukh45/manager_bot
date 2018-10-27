import motor.motor_asyncio


class MongoDBConnector:
    """Handles connection with a MongoDB database."""

    def __init__(self, srv_url, db_name, loop):
        self.client = motor.motor_asyncio.AsyncIOMotorClient(srv_url, io_loop=loop)
        self.db = self.client[db_name]

    async def put_member(self, member_id):
        """Store a Discord guild member ID."""
        await self.db.members.insert_one({'id': member_id})

    async def get_all_members(self):
        """Retrieve a list of all member IDs from the database."""
        cursor = self.db.members.find()
        members = await cursor.to_list(length=None)
        return [member['id'] for member in members]

    async def remove_member(self,member_id):
        await self.db.members.delete_one({'id':member_id})
