# PloitZ-Discord-Bot

PloitZ is a versatile and powerful Discord bot designed to enhance the experience of your community server. With a wide range of commands, PloitZ helps with moderation, utility, fun, and more. Whether you're managing a small group of friends or a large public server, PloitZ has got you covered.

## Features

### Essential Commands
- **/help**: All commands and what they do.
#### Moderation Commands
- **/ban [user] [reason]**: Bans a user from the server.
- **/kick [user] [reason]**: Kicks a user from the server.
- **/mute [user] [duration] [reason]**: Mutes a user for a specified duration. 
- **/unmute [user]**: Unmutes a user. 
- **/warn [user] [reason]**: Issues a warning to a user. 
- **/clear [number]**: Deletes a specified number of messages from a channel. 
- **/lock [channel]**: Locks a channel, preventing users from sending messages. 
- **/unlock [channel]**: Unlocks a channel. 

#### Utility Commands
- **/ping**: Checks the bot's latency.
- **/user [@user]**: Displays information about a specific user. 
- **/serverinfo**: Displays information about the server.
- **/roleinfo [@role]**: Provides information about a specific role. 
- **/poll [question] [option1] [option2] ...**: Creates a poll for users to vote on.
  
### Fun and Engagement Commands
- **/meme**: Fetches a random meme. 
- **/joke**: Tells a random joke. 
- **/quote**: Sends a random inspirational quote. 
- **/8ball [question]**: Magic 8-ball command for fun predictions. 
- **/roll [number]**: Rolls a random number between 1 and the specified number.

#### Leveling and Economy (coming soon)
- **/rank**: Displays the user’s rank and experience points.
- **/leaderboard**: Shows the top-ranked users in the server. 
- **/xp**: Displays users XP.

#### Event and Reminder Commands
- **/event [details]**: Creates a server event with specific details. 

#### Administration Commands
- **/setprefix [new prefix]**: Changes the bot’s command prefix. (coming soon)
- **/disablecommand [command]**: Disables a specific command in the server. (coming soon)
- **/enablecommand [command]**: Enables a previously disabled command. (coming soon)
- **/logchannel [#channel]**: Sets a specific channel for logging moderation actions and events. (coming soon)

## Best Practices

- **Permissions**: Ensure commands have appropriate permission checks to prevent misuse.
- **Help Command**: Implement a help command to list all available commands and their usage.
- **Feedback**: Provide feedback messages to users for successful and unsuccessful command executions.

## Installation and Setup

To run PloitZ bot locally or on your server, follow these steps:

1. **Clone the repository:**
   ```bash
   git clone https://github.com/unofficialdxnny/PloitZ-Discord-Bot.git
   cd PloitZ-Discord-Bot

2. **Install dependencies:**
    ```
    pip install -r requirements.txt
    ```

3. **Configure environment variables:**

    Create a .env file in the root directory with the following variables:

    ```env
    TOKEN=your_bot_token_here
    TEST_GUILD_ID=your_test_guild_id_here
    TICKETS_CATEGORY=your_tickets_category_id_here
    WELCOME_CHANNEL_ID=your_welcome_channel_id_here
    RULES_CHANNEL_ID=your_rules_channel_id_here
    VERIFICATION_CHANNEL_ID=your_verification_channel_id_here
    MEMBERS_ROLE_ID=your_members_role_id_here
    UNVERIFIED_ROLE_ID=your_unverified_role_id_here
    ```

4. **Run the bot:**
    ```
    python PloitZ.py
    ```

## Contributing
Contributions are welcome! If you have suggestions, feature requests, or find a bug, please open an issue or submit a pull request.
