# Mass Communication Library
This library can be used for programmatically communicating over a wide range of platforms.  It allows you to send mass messages without writing any code.  It also supports sending personalized messages-- all you have to do is write a single function that pulls out user-specific information from a set of input data.
## Basic Mass Messaging
### Configuration
Default senders for respective platforms may be configured with environment variables.  Simply `export COMM_<platform>_SENDER=<filepath>`, where `platform` is the name of the platform as seen in `comm/platforms.py` (in all caps) and `filepath` is the path to a file containing sender data specific to the platform.  Below are examples of configuration for the existing modules.
#### Slack
```json
{
    "username": "example-bot",
    "token": "xoxb-312614143591-GPT7F4VwAH3UD0KtLgPoPsa6"
}
```
#### Email
```json
{
    "address": "example@gmail.com",
    "password": "example",
    "smtp": {
        "host": "smtp.gmail.com",
        "port": 587
    }
}
```
### Command Line Interface
To send the same content to a list of recipients, run `python3 -m comm.basic <platform> <recipients> <content>`, where `platform` is the name of the platform as seen in `comm/platforms.py` and `content` is the raw content of the message.  The `recipients` argument should be a space-delimited list of recipients.  For most platforms, a recipient can be described with a simple identifier such as a username or address.  However, some platforms may require additional information to describe a recipient.  In such cases, recipients should be specified with platform-specific JSON.  The sender JSON can be specified with the `--sender` flag.

Note: If you need the ability to run this as a script and not a module, just create a file adjacent to the `comm` package with the following contents:
```python
from comm.basic import CLI, send_to_all
send_to_all(**CLI().get_args())
```
You can then run the file as a script.
#### Examples
```bash
python3 -m comm.basic slack '{"username": "@example.user"}' 'Hello, World!' --sender '{"username": "example-bot", "token": "xoxb-312614143591-GPT7F4VwAH3UD0KtLgPoPsa6"}'
```
Now let's assume you've set up the same sender in config, and created a file called `mass_message.py` that runs `comm.basic` as a script.  The following command will then have the same effect:
```bash
python3 mass_message.py slack @example.user 'Hello, World!'
```
### Programmatic Usage
The key function in this module, `send_to_all`, can be imported and used in other python scripts.  Its arguments are the same as what would be entered into command line, except that textual data representations should be replaced with their corresponding python data representations, e.g. dictionaries and lists rather than JSON or YAML.
## Templated Mass Messaging
To send a message template filled with personalized information for each recipient, use the `comm.templated` module.  The `send_to_all` function takes in a message template and some JSON data, and attempts to fill the template with data corresponding to each recipient.  Recipients with no corresponding data will be skipped, and will not be sent messages.  You'll need to write a function that extracts a user's information from the data and returns the strings used to fill the template.  If no information is found for the given recipient, it should return `None`.  In this function, you can also use logging to report when your input data contains information that has no associated user in your user table.  This allows you update the table, and then rerun your script for the new users.
### Command Line Interface
The CLI for templated messaging inherits all functionality from the basic CLI described above, and adds some additional requirements and capabilities.  The `content` argument is used for the message template.  The data used to fill the template should be specified as JSON and may either be piped into the script or specified as an argument with the optional `--data` flag.  The user table, which serves the purpose of associating multiple usernames across multiple platforms with a single user, can be specified by setting an environment variable called `COMM_USER_TABLE` to point to a YAML file.  Alternatively, the YAML text can be entered directly with the `--user-table` flag.  The table is used for filling message templates and for inferring recipients based on the given data when none are specified.  That being the case, the `--recipients` argument is an optional flag that may be used to specify to a subset of all possible recipients.
### Programmatic Usage
In order to do anything meaningful with `comm.templated`, you'll need to manually call its `send_to_all` function.  Programmatic usage of the `send_to_all` function is similar to that of `comm.basic.send_to_all`, but takes in three additional arguments:
- templating_data: The full set of data used to fill the template
- user_table_data: A list of users, where a user is a mapping of platform names to lists of usernames
- template_input_builder: A function that returns the strings used to fill the message content template with personalized information from provided data, or returns `None` if no relevant information is found

You can create this information on the fly in your scripts, or make use of the existing command line interface.
### Example
This is the script used for sending out the expiration status of GCE instances.  It uses `comm.templated.CLI` to produce most of the arguments to `send_to_all`, and passes in `template_input_builder`, which must be done programmatically.
```python
def get_template_inputs(user, data):
    owners = [owner for owner in user.get_ids('gce') if owner in data]
    if not owners:
        return None
    instances = [instance for owner in owners for instance in data[owner]]
    instance_template = 'Expiration for instance \'{}\': {}\n'
    data_str = ''
    for instance in instances:
        data_str += instance_template.format(instance['name'],
                                             instance['expiration'])
    return ', '.join(owners), data_str


if __name__ == '__main__':
    from comm.templated import CLI, send_to_all
    send_to_all(template_input_builder=get_template_inputs,
                **CLI().get_args())
```
Here's an example usage of this script:
```bash
echo '{"example-gce-owner": [{"name": "example-instance-name", "expiration": "example-expiration"}]}' | python3 expiration_comm.py slack 'Hi {0}. {1}'
```
The data for this use case is a mapping of GCE usernames to lists of instance names and expirations.  It would normally be piped from another script, but it's shown here for clarity.  The slack user(s) associated with the GCE username "example-gce-owner" will receive the following message: "Hi example-gce-owner. Expiration for instance 'example-instance-name': example-expiration".
### How it Works
The `comm.templated.send_to_all` function calls `template_input_builder` for each recipient to get the personalized inputs to the message template.  Each call to `template_input_builder` is passed `user` and `data` as named arguments (which can be discarded in the signature of `template_input_builder` if not needed).  The `data` argument holds the entirety of the templating data used by the function.  The `user` argument holds an instance of `comm.user_table.User`, which is essentially a mapping of each platform name (as seen in `comm/platforms.py`) to a list containing the user's username(s) for that platform.  For convenience, `comm.user_table.User` comes with a `get_ids` method which returns the user's username(s) for the given platform.  Your template input builder should know how to extract information from the data and return a tuple containing the appropriate strings for filling in the template.

At the bottom of the above example, you'll notice that the script makes use of `comm.templated.CLI`.  The `get_args` method of `comm.templated.CLI` returns a dictionary containing the resources used by the script.  Just unpack this dictionary into a call to `comm.templated.send_to_all` along with `template_input_builder`.
### Usage Summary
1. Create a script for your specific use case.
2. In the script, write a function that takes in a user and data in a predictable format, and returns a tuple of strings used to fill the message template for the given user, or `None` if there is no data for the given user.
3. Use `comm.templated.CLI.get_args` to load the inputs to the script, and pass them into a call to `comm.templated.send_to_all` along with your `template_input_builder` function from step 2.
3. Run `<data_source> | python3 <script_name> <platform> <content>`, where `data_source` is a command that outputs your JSON data, and `script_name` is the name of the script you've written for your use case.
## Adding Platforms
Adding support for new platforms is very straightforward.  Simply implement subclasses for the abstract `User`, `ClientUser`, and `Platform` classes in `comm/platform.py`, and add the platform name and adapter (the `Platform` subclass) to `platforms.py`.  Be wary of the readme as you design your platform interface to ensure that you leverage the features of the script as much as possible.  For example, ensure that your recipients can be constructed from either JSON or a username if possible, and that reusable resources such as servers are used efficiently (see `comm/email.py`).
