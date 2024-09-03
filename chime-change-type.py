"""Sample script that uses the ring-doorbell API to change the in-home chime type."""

import asyncio
import getpass
import json
from pathlib import Path
import time

from ring_doorbell import Auth, AuthenticationError, Requires2FAError, Ring

user_agent = "ring-samples-1.0"  # Change this
cache_file = Path(user_agent + ".token.cache")


def token_updated(token) -> None:
    cache_file.write_text(json.dumps(token))


def otp_callback():
    return input("2FA code: ")


async def do_auth():
    username = input("Username: ")
    password = getpass.getpass("Password: ")
    auth = Auth(user_agent, None, token_updated)
    try:
        await auth.async_fetch_token(username, password)
    except Requires2FAError:
        await auth.async_fetch_token(username, password, otp_callback())
    return auth


async def main() -> None:
    if cache_file.is_file():  # auth token is cached
        auth = Auth(user_agent, json.loads(cache_file.read_text()), token_updated)
        ring = Ring(auth)
        try:
            await ring.async_create_session()  # auth token still valid
        except AuthenticationError:  # auth token has expired
            auth = await do_auth()
    else:
        auth = await do_auth()  # Get new auth token
        ring = Ring(auth)

    await ring.async_update_data()

    # Fetch all available doorbells
    devices = ring.devices()
    doorbells=devices['doorbots']

    # Flip the status of the in-home chime for each doorbell
    for doorbell in list(doorbells):
        await doorbell.async_update_health_data()
        print()
        print()
        print('Name:       %s' % doorbell.name)
        print('Family:     %s' % doorbell.family)
        print('ID:         %s' % doorbell.id)
        print('In-Home Chime Type: %s' % doorbell.existing_doorbell_type)
        print('In-Home Chime Status: %s' % doorbell.existing_doorbell_type_enabled)
        print('In-Home Chime Duration: %s' % doorbell.existing_doorbell_type_duration)
        print()
        print()
        while True:
            # Prompt the user for input
            user_choice = input("Please select a chime type (0 for Mechanical, 1 for Digital, 2 for Not Present): ")

            try:
                user_choice = int(user_choice)

                # Check if the input is valid
                if user_choice in [0, 1, 2]:
                    print('Changing In-Home Chime Type to %s' % user_choice)
                    await doorbell.async_set_existing_doorbell_type(user_choice)
                    time.sleep(2)
                    print()
                    print('Changes complete...')
                    print('In-Home Chime Type: %s' % doorbell.existing_doorbell_type)
                    print('In-Home Chime Status: %s' % doorbell.existing_doorbell_type_enabled)
                    print('In-Home Chime Duration: %s' % doorbell.existing_doorbell_type_duration)
                    break
                else:
                    print("Invalid selection. Please choose 0, 1, or 2.")
            except ValueError:
                print("Invalid input. Please enter a number (0, 1, or 2).")

    await auth.async_close()


if __name__ == "__main__":
    asyncio.run(main())
