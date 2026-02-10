"""
Initialize database with sample data.

Run with: python scripts/init_data.py

To add predefined users:
  python scripts/init_data.py --add-user username client_name
"""

import argparse
import asyncio
import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))

from sqlalchemy import select

from app.database.connection import DatabaseSessionManager, init_db
from app.database.models import Client, PredefinedUser, Project


async def init_sample_data() -> None:
    """Create sample clients and projects."""
    print("=" * 50)
    print("Initializing database with sample data")
    print("=" * 50)
    
    # Initialize database
    await init_db()
    
    async with DatabaseSessionManager() as session:
        # Check if data already exists
        result = await session.execute(select(Client).limit(1))
        if result.scalar_one_or_none():
            print("\n⚠️  Data already exists. Skipping initialization.")
            print("   Delete the database file to reinitialize.")
            return
        
        # Create sample clients
        client1 = Client(name="Demo Company")
        client2 = Client(name="Test Corp")
        client3 = Client(name="Acme Inc")
        session.add_all([client1, client2, client3])
        await session.flush()
        
        print(f"\n✅ Created {3} clients")
        
        # Create sample projects with invite codes
        projects = [
            Project(
                client_id=client1.id, 
                name="Main Project", 
                invite_code="DEMO001"
            ),
            Project(
                client_id=client1.id, 
                name="Beta Project", 
                invite_code="DEMO002"
            ),
            Project(
                client_id=client2.id, 
                name="Production", 
                invite_code="TEST001"
            ),
            Project(
                client_id=client2.id, 
                name="Staging", 
                invite_code="TEST002"
            ),
            Project(
                client_id=client3.id, 
                name="Analytics Platform", 
                invite_code="ACME001"
            ),
        ]
        session.add_all(projects)
        await session.commit()
        
        print(f"✅ Created {len(projects)} projects")
        
        print("\n" + "=" * 50)
        print("Sample invite codes:")
        print("=" * 50)
        for p in projects:
            # Reload to get client name
            await session.refresh(p)
            result = await session.execute(
                select(Client).where(Client.id == p.client_id)
            )
            client = result.scalar_one()
            print(f"  {p.invite_code}: {client.name} / {p.name}")
        
        print("\n✅ Initialization complete!")
        print("\nTo test, send to your bot:")
        print("  /start DEMO001")


async def add_predefined_user(username: str, client_name: str) -> None:
    """
    Add a predefined user mapping.
    
    Args:
        username: Telegram username (without @)
        client_name: Client company name
    """
    # Initialize database
    await init_db()
    
    # Normalize username
    username = username.lstrip("@").lower()
    
    async with DatabaseSessionManager() as session:
        # Find client by name
        result = await session.execute(
            select(Client).where(Client.name == client_name)
        )
        client = result.scalar_one_or_none()
        
        if not client:
            print(f"❌ Client '{client_name}' not found.")
            print("\nAvailable clients:")
            result = await session.execute(select(Client))
            for c in result.scalars():
                print(f"  - {c.name}")
            return
        
        # Check if user already exists
        result = await session.execute(
            select(PredefinedUser)
            .where(PredefinedUser.tg_username == username)
        )
        existing = result.scalar_one_or_none()
        
        if existing:
            print(f"⚠️  User @{username} already mapped to client ID {existing.client_id}")
            return
        
        # Create predefined user
        predefined = PredefinedUser(
            tg_username=username,
            client_id=client.id
        )
        session.add(predefined)
        await session.commit()
        
        print(f"✅ Added predefined user: @{username} → {client.name}")


async def list_predefined_users() -> None:
    """List all predefined users."""
    await init_db()
    
    async with DatabaseSessionManager() as session:
        result = await session.execute(
            select(PredefinedUser, Client)
            .join(Client, PredefinedUser.client_id == Client.id)
        )
        rows = result.all()
        
        if not rows:
            print("No predefined users found.")
            return
        
        print("=" * 50)
        print("Predefined users:")
        print("=" * 50)
        for predefined, client in rows:
            print(f"  @{predefined.tg_username} → {client.name}")


async def add_predefined_users_batch(mapping: dict) -> None:
    """
    Add multiple predefined users at once.
    
    Args:
        mapping: Dict of {client_name: [username1, username2, ...]}
    """
    await init_db()
    
    async with DatabaseSessionManager() as session:
        added = 0
        
        for client_name, usernames in mapping.items():
            # Find client
            result = await session.execute(
                select(Client).where(Client.name == client_name)
            )
            client = result.scalar_one_or_none()
            
            if not client:
                print(f"⚠️  Client '{client_name}' not found, skipping {len(usernames)} users")
                continue
            
            for username in usernames:
                username = username.lstrip("@").lower()
                
                # Check if exists
                result = await session.execute(
                    select(PredefinedUser)
                    .where(PredefinedUser.tg_username == username)
                )
                if result.scalar_one_or_none():
                    print(f"⚠️  @{username} already exists, skipping")
                    continue
                
                predefined = PredefinedUser(
                    tg_username=username,
                    client_id=client.id
                )
                session.add(predefined)
                added += 1
                print(f"✅ @{username} → {client.name}")
        
        await session.commit()
        print(f"\n✅ Added {added} predefined users")


def main():
    parser = argparse.ArgumentParser(description="Initialize database and manage predefined users")
    
    subparsers = parser.add_subparsers(dest="command", help="Commands")
    
    # init command
    subparsers.add_parser("init", help="Initialize database with sample data")
    
    # add-user command
    add_user_parser = subparsers.add_parser("add-user", help="Add a predefined user")
    add_user_parser.add_argument("username", help="Telegram username (without @)")
    add_user_parser.add_argument("client", help="Client company name")
    
    # list-users command
    subparsers.add_parser("list-users", help="List predefined users")
    
    args = parser.parse_args()
    
    if args.command == "init" or args.command is None:
        asyncio.run(init_sample_data())
    elif args.command == "add-user":
        asyncio.run(add_predefined_user(args.username, args.client))
    elif args.command == "list-users":
        asyncio.run(list_predefined_users())
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
