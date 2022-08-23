![](logo-enterprise-search.png)

[Elastic Enterprise Search](https://www.elastic.co/guide/en/enterprise-search/current/index.html) | [Elastic Workplace Search](https://www.elastic.co/guide/en/workplace-search/current/index.html)

# Microsoft Outlook connector package

Use this _Elastic Enterprise Search Microsoft Outlook connector package_ to deploy and run a Microsoft Outlook connector on your own infrastructure. The connector extracts and syncs data from [Microsoft Exchange Outlook](https://docs.microsoft.com/en-us/exchange/exchange-server?view=exchserver-2019) and [Microsoft Office365 Outlook](https://docs.microsoft.com/en-us/microsoft-365/?view=o365-worldwide) application. The data is indexed into a Workplace Search content source within an Elastic deployment.

⚠️ _This connector package is a **beta** feature._
Beta features are subject to change and are not covered by the support SLA of generally available (GA) features. Elastic plans to promote this feature to GA in a future release.

ℹ️ _This connector package requires a compatible Elastic subscription level._
Refer to the Elastic subscriptions pages for [Elastic Cloud](https://www.elastic.co/subscriptions/cloud) and [self-managed](https://www.elastic.co/subscriptions) deployments.

**Table of contents:**

- [Setup and basic usage](#setup-and-basic-usage)
  - [Gather Microsoft Outlook details](#gather-microsoft-outlook-details)
  - [Gather Elastic details](#gather-elastic-details)
  - [Create a Workplace Search API key](#create-a-workplace-search-api-key)
  - [Create a Workplace Search content source](#create-a-workplace-search-content-source)
  - [Choose connector infrastructure and satisfy dependencies](#choose-connector-infrastructure-and-satisfy-dependencies)
  - [Install the connector](#install-the-connector)
  - [Configure the connector](#configure-the-connector)
  - [Test the connection](#test-the-connection)
  - [Sync data](#sync-data)
  - [Log errors and exceptions](#log-errors-and-exceptions)
  - [Schedule recurring syncs](#schedule-recurring-syncs)
- [Troubleshooting](#troubleshooting)
  - [Troubleshoot extraction](#troubleshoot-extraction)
  - [Troubleshoot Access Token Generation](#troubleshoot-access-token-generation)
- [Advanced usage](#advanced-usage)
  - [Customize extraction and syncing](#customize-extraction-and-syncing)
  - [Use document-level permissions (DLP)](#use-document-level-permissions-dlp)
- [Connector reference](#connector-reference)
  - [Data extraction and syncing](#data-extraction-and-syncing)
  - [Sync operations](#sync-operations)
  - [Command line interface (CLI)](#command-line-interface-cli)
  - [Configuration settings](#configuration-settings)
  - [Enterprise Search compatibility](#enterprise-search-compatibility)
  - [Runtime dependencies](#runtime-dependencies)
- [Connector Limitations](#connector-limitations)

## Setup and basic usage

Complete the following steps to deploy and run the connector:

1. [Gather Microsoft Outlook details](#gather-microsoft-outlook-details)
2. [Gather Elastic details](#gather-elastic-details)
3. [Create a Workplace Search API key](#create-a-workplace-search-api-key)
4. [Create a Workplace Search content source](#create-a-workplace-search-content-source)
5. [Choose connector infrastructure and satisfy dependencies](#choose-connector-infrastructure-and-satisfy-dependencies)
6. [Install the connector](#install-the-connector)
7. [Configure the connector](#configure-the-connector)
8. [Test the connection](#test-the-connection)
9. [Sync data](#sync-data)
10. [Log errors and exceptions](#log-errors-and-exceptions)
11. [Schedule recurring syncs](#schedule-recurring-syncs)

The steps above are relevant to all users. Some users may require additional features. These are covered in the following sections:

- [Customize extraction and syncing](#customize-extraction-and-syncing)
- [Use document-level permissions (DLP)](#use-document-level-permissions-dlp)

### Gather Microsoft Outlook details

It is necessary to identify whether you are using Microsoft _Exchange_ Outlook or Microsoft _Office365_ Outlook and configure the parameter `connector_platform_type`. You'll need to gather different details based on this. 

For Microsoft _Exchange_ Outlook, collect the following information:

- The IP address or Hostname of the Microsoft Exchange active directory host.
- The IP address or Hostname of the Microsoft Exchange Server host.
- The username the connector will use to log in to Microsoft Exchange Outlook.
- The password the connector will use to log in to Microsoft Exchange Outlook.
- The domain of the Microsoft Exchange Server host.
- The path of the SSL certificate if Microsoft Exchange Server host is secured.

ℹ️ The username and password must be the admin account for the Microsoft Exchange server.

For Microsoft _Office365_ Outlook, collect the following information:

- The `client id`, `tenant id` and `client secret` will be used to generate access tokens and fetch users details.

Later, you will [configure the connector](#configure-the-connector) with these values.

Some connector features require additional details. Review the following documentation if you plan to use these features:

- [Customize extraction and syncing](#customize-extraction-and-syncing)
- [Use document-level permissions (DLP)](#use-document-level-permissions-dlp)

### Gather Elastic details

First, ensure your Elastic deployment is [compatible](#enterprise-search-compatibility) with the Microsoft Outlook connector package.

Next, determine the [Enterprise Search base URL](https://www.elastic.co/guide/en/enterprise-search/current/endpoints-ref.html#enterprise-search-base-url) for your Elastic deployment.

Later, you will [configure the connector](#configure-the-connector) with this value.

You also need a Workplace Search API key and a Workplace Search content source ID. You will create those in the following sections.

If you plan to use document-level permissions, you will also need user identity information. See [Use document-level permissions (DLP)](#use-document-level-permissions-dlp) for details.

### Create a Workplace Search API key

Each Microsoft Outlook Server connector authorizes its connection to Elastic using a Workplace Search API key.

Create an API key within Kibana. See [Workplace Search API keys](https://www.elastic.co/guide/en/workplace-search/current/workplace-search-api-authentication.html#auth-token).

### Create a Workplace Search content source

Each Microsoft Outlook Server connector syncs data from Microsoft Outlook Server into a Workplace Search content source.

Create a content source within Kibana:

1. Navigate to **Enterprise Search** → **Workplace Search** → **Sources** → **Add Source** → **Custom API Source**.
2. Name your Content Source, (e.g. Microsoft Outlook Connector).
3. Choose **Configure Microsoft Outlook Connector**.

For more details please refer [Elastic Documentation for creating a custom API source](https://www.elastic.co/guide/en/workplace-search/current/workplace-search-custom-api-sources.html#create-custom-source).

Record the ID of the new content source. This value is labeled *Source Identifier* within Kibana. Later, you will [configure the connector](#configure-the-connector) with this value.

**Alternatively**,  you can use the connector’s `bootstrap` command to create the content source. See [`bootstrap` command](#bootstrap-command).

### Choose connector infrastructure and satisfy dependencies

After you’ve prepared the two services, you are ready to connect them.

Provision a Windows, MacOS, or Linux server for your Microsoft Outlook connectors.

The infrastructure must provide the necessary runtime dependencies. See [Runtime dependencies](#runtime-dependencies).

Clone or copy the contents of this repository to your infrastructure.

### Install the connector

After you’ve provisioned infrastructure and copied the package, use the provided `make` target to install the connector:

```shell
make install_package
```

This command runs as the current user and installs the connector and its dependencies.
Note: By Default, the package installed supports Enterprise Search version 8.0 or above. In order to use the connector for older versions of Enterprise Search(less than version 8.0) use the `ES_VERSION_V8` argument while running the `make install_package` or `make install_locally` command:

```shell
make install_package ES_VERSION_V8=no
```

ℹ️ Within a Windows environment, first install `make`:

Note: If you are running the connector on Windows, please ensure Microsoft Visual C++ 14.0 or greater is installed.

```
winget install -e --id GnuWin32.Make
```

Next, ensure the `ees_microsoft_outlook` executable is on your `PATH`. For example, on macOS:

```shell
export PATH=/Users/$USER/Library/Python/3.8/bin:$PATH
```

The following table provides the installation location for each operating system (note Python version 3.8):

| Operating system | Installation location                                        |
| ---------------- | ------------------------------------------------------------ |
| Linux            | `./local/bin`                                                |
| macOS            | `/Users/<user_name>/Library/Python/3.8/bin`                  |
| Windows          | `\Users\<user_name>\AppData\Roaming\Python\Python38\Scripts` |

### Configure the connector

You must configure the connector to provide the information necessary to communicate with each service. You can provide additional configuration to customize the connector for your needs.

Create a [YAML](https://yaml.org/) configuration file at any pathname. Later, you will include the [`-c` option](#-c-option) when running [commands](#command-line-interface-cli) to specify the pathname to this configuration file.

_Alternatively, in Linux environments only_, locate the default configuration file created during installation. The file is named `microsoft_outlook_connector.yml` and is located within the `config` subdirectory where the package files were installed. See [Install the connector](#install-the-connector) for a listing of installation locations by operating system. When you use the default configuration file, you do not need to include the `-c` option when running commands.

After you’ve located or created the configuration file, populate each of the configuration settings. Refer to the [settings reference](#configuration-settings). You must provide a value for all required settings.

Use the additional settings to customize the connection and manage features such as document-level permissions. See:

- [Customize extraction and syncing](#customize-extraction-and-syncing)
- [Use document-level permissions (DLP)](#use-document-level-permissions-dlp)

### Test the connection

After you’ve configured the connector, you can test the connection between Elastic and Microsoft Outlook. Use the following `make` target to test the connection:

```shell
make test_connectivity
```

### Sync data

After you’ve confirmed the connection between the two services, you are ready to sync data from Microsoft Outlook to Elastic.

The following table lists the available [sync operations](#sync-operations), as well as the [commands](#command-line-interface-cli) to perform the operations.

| Operation                             | Command                                         |
| ------------------------------------- | ----------------------------------------------- |
| [Incremental sync](#incremental-sync) | [`incremental-sync`](#incremental-sync-command) |
| [Full sync](#full-sync)               | [`full-sync`](#full-sync-command)               |
| [Deletion sync](#deletion-sync)       | [`deletion-sync`](#deletion-sync-command)       |
| [Permission sync](#permission-sync)   | [`permission-sync`](#permission-sync-command)   |

Begin syncing with an *incremental sync*. This operation begins [extracting and syncing content](#data-extraction-and-syncing) from Microsoft Outlook to Elastic. If desired, [customize extraction and syncing](#customize-extraction-and-syncing) for your use case.

Review the additional sync operations to learn about the different types of syncs. Additional configuration is required to use [document-level permissions](#use-document-level-permissions-dlp).

You can use the command line interface to run sync operations on demand, but you will likely want to [schedule recurring syncs](#schedule-recurring-syncs).

### Log errors and exceptions

The various [sync commands](#command-line-interface-cli) write logs to standard output and standard error.

To persist logs, redirect standard output and standard error to a file. For example:

```shell
ees_microsoft_outlook -c ~/config.yml incremental-sync >>~/incremental-sync.log 2>&1
```

You can use these log files to implement your own monitoring and alerting solution.

Configure the log level using the [`log_level` setting](#log_level).

### Schedule recurring syncs

Use a job scheduler, such as `cron`, to run the various [sync commands](#command-line-interface-cli) as recurring syncs.

The following is an example crontab file in linux:

```crontab
PATH=/home/<user_name>/.local/bin
0 */2 * * * ees_microsoft_outlook -c ~/config.yml incremental-sync >>~/incremental-sync.log 2>&1
0 0 */2 * * ees_microsoft_outlook -c ~/config.yml full-sync >>~/full-sync.log 2>&1
0 * * * * ees_microsoft_outlook -c ~/config.yml deletion-sync >>~/deletion-sync.log 2>&1
*/5 * * * * ees_microsoft_outlook -c ~/config.yml permission-sync >>~/permission-sync.log 2>&1
```

This example redirects standard output and standard error to files, as explained here: [Log errors and exceptions](#log-errors-and-exceptions).

Use this example to create your own crontab file. Manually add the file to your crontab using `crontab -e`. Or, if your system supports cron.d, copy or symlink the file into `/etc/cron.d/`.

⚠️ **Note**: It's possible that scheduled jobs may overlap.
To avoid multiple crons running concurrently, you can use [flock](https://manpages.debian.org/testing/util-linux/flock.1.en.html) with cron to manage locks. The `flock` command is part of the `util-linux` package. You can install it with `yum install util-linux`
or `sudo apt-get install -y util-linux`.
Using flock ensures the next scheduled cron runs only after the current one has completed execution. 

Let's consider an example of running incremental-sync as a cron job with flock:

```crontab
0 */2 * * * /usr/bin/flock -w 0 /var/cron.lock ees_microsoft_outlook -c ~/config.yml incremental-sync >>~/incremental-sync.log 2>&1
```

Note: If the flock is added for multiple commands in crontab, make sure you mention different lock names(eg: /var/cron_indexing.lock in the above example) for each job else the execution of one command will prevent other command to execute.

## Troubleshooting

To troubleshoot an issue, first view your [logged errors and exceptions](#log-errors-and-exceptions).

Use the following sections to help troubleshoot further:

- [Troubleshoot extraction](#troubleshoot-extraction)
- [Troubleshoot Access Token Generation](#troubleshoot-access-token-generation)

If you need assistance, use the Elastic community forums or Elastic support:

- [Enterprise Search community forums](https://discuss.elastic.co/c/enterprise-search/84)
- [Elastic Support](https://support.elastic.co)

### Troubleshoot extraction

The following sections provide solutions for content extraction issues.

#### Issues extracting content from attachments

The connector uses the [Tika module](https://pypi.org/project/tika/) for parsing file contents from attachments. [Tika-python](https://github.com/chrismattmann/tika-python) uses Apache Tika REST server. To use this library, you need to have Java 7+ installed on your system as tika-python starts up the Tika REST server in the background.

At times, the TIKA server fails to start hence content extraction from attachments may fail. To avoid this, make sure Tika is running in the background.

#### Issues extracting content from images

Tika Server also detects contents from images by automatically calling Tesseract OCR. To allow Tika to also extract content from images, you need to make sure tesseract is on your path and then restart tika-server in the background (if it is already running). For example, on a Unix-like system, try:

```shell
ps aux | grep tika | grep server # find PID
kill -9 <PID>
```

To allow Tika to extract content from images, you need to manually install Tesseract OCR.

## Advanced usage

The following sections cover additional features that are not covered by the basic usage described above.

After you’ve set up your first connection, you may want to further customize that connection or scale to multiple connections.

- [Customize extraction and syncing](#customize-extraction-and-syncing)
- [Use document-level permissions (DLP)](#use-document-level-permissions-dlp)

## Customize extraction and syncing

By default, each connection syncs all [supported Microsoft Outlook data](#data-extraction-and-syncing) across all Microsoft Outlook applications.

You can also customize which objects are synced, and which fields are included and excluded for each object. [Configure](#configure-the-connector) the setting [`objects`](#objects).

Finally, you can set custom timestamps to control which objects are synced, based on their created or modified timestamps. [Configure](#configure-the-connector) the following settings:

- [`start_time`](#start_time)
- [`end_time`](#end_time)

### Troubleshoot Access Token Generation

The following sections provide the solution for issues related to access token generation.

#### Disable Multi-factor Authentication
1. Go to **Microsoft Azure AD -> Properties**.
2. Go to **Manage Security defaults**, disable the security, and save the changes.
3. Go to **Users** and create a new user with global permissions from assignees roles.
4. Go to **Microsoft Outlook Azure AD conditional access** and create a new policy:
- **Name:** Name of the policy
- **Users or workload identities:** include "allusers" and exclude the newly created users (this step will disable MFA for all excluded users).
- **Cloud apps or actions:** include "All cloud apps"
- **Grant:** select "grant access" with Require "multi-factor authentication" enabled and from multiple controls select "Require all the selected controls"

#### Add permissions to Microsoft Azure Platform
1. Check the configuration file and verify all Microsoft Outlook settings configuration values are set correctly.
2. If configuration values are set correctly, go to your application on Microsoft Azure Platform and verify all permissions are added as per the permission listed below and have the admin consent to each permission.
- `User.Read` (Delegated)
- `User.Read.All` (Delegated and Application)
- `full_access_as_app` (Application)

#### Add permissions to Microsoft Exchange Server
1. Check the configuration file and verify all Microsoft Outlook settings configuration values are set correctly.
2. If configuration values are set correctly:
    1. Go to your application on Microsoft Exchange Server
    2. Verify permissions under admin roles 
    3. Add Application Impersonation in the impersonation section
    4. Include admin user in member section.

### Use document-level permissions (DLP)

Complete the following steps to use document-level permissions:

1. Enable document-level permissions
1. Map user identities
1. Sync document-level permissions data

#### Enable document-level permissions

Within your configuration, enable document-level permissions using the following setting: [`enable_document_permission`](#enable_document_permission).

#### Map user identities

Copy to your server a CSV file that provides the mapping of user identities. The file must follow this format:

- First column: Microsoft Outlook username
- Second column: Elastic username

Then, configure the location of the CSV file using the following setting: [`connector.user_mapping`](#connectoruser_mapping).

#### Sync document-level permissions data

Sync document-level permissions data from Microsoft Outlook to Elastic.

The following sync operations include permissions data:

- [Permission sync](#permission-sync)
- [Full sync](#full-sync)
- [Incremental sync](#incremental-sync)

Sync this information continually to ensure correct permissions. See [Schedule recurring syncs](#schedule-recurring-syncs).

## Connector reference

The following reference sections provide technical details:

- [Data extraction and syncing](#data-extraction-and-syncing)
- [Sync operations](#sync-operations)
- [Command line interface (CLI)](#command-line-interface-cli)
- [Configuration settings](#configuration-settings)
- [Enterprise Search compatibility](#enterprise-search-compatibility)
- [Runtime dependencies](#runtime-dependencies)

### Data extraction and syncing

Each Microsoft Outlook connector extracts and syncs the following data from Microsoft Outlook:

- Mails
- Calendar
- Tasks
- Contacts

The connector handles Microsoft Outlook pages comprised of various web parts, it extracts content from various document formats, and it performs optical character recognition (OCR) to extract content from images.

You can customize extraction and syncing per connector. See [Customize extraction and syncing](#customize-extraction-and-syncing).

### Sync operations

The following sections describe the various operations to [sync data](#sync-data) from Microsoft Outlook to Elastic.

#### Incremental sync

Syncs to Enterprise Search all [supported Microsoft Outlook data](#data-extraction-and-syncing) *created or modified* since the previous incremental sync.

Perform this operation with the [`incremental-sync` command](#incremental-sync-command).

#### Full sync

Syncs to Enterprise Search all [supported Microsoft Outlook data](#data-extraction-and-syncing) *created or modified* since the configured [`start_time`](#start_time). Continues until the current time or the configured [`end_time`](#end_time).

Perform this operation with the [`full-sync` command](#full-sync-command).

#### Deletion sync

Deletes from Enterprise Search all [supported Microsoft Outlook data](#data-extraction-and-syncing) *deleted* since the previous deletion sync.

Perform this operation with the [`deletion-sync` command](#deletion-sync-command).

#### Permission sync

Syncs to Enterprise Search all Microsoft Outlook document permissions since the previous permission sync.

When [using document-level permissions (DLP)](#use-document-level-permissions-dlp), use this operation to sync all updates to users within Microsoft Outlook.

Perform this operation with the [`permission-sync` command](#permission-sync-command).

### Command line interface (CLI)

Each Microsoft Outlook Server connector has the following command line interface (CLI):

```shell
ees_microsoft_outlook [-c <pathname>] <command>
```

#### `-c` option

The pathname of the [configuration file](#configure-the-connector) to use for the given command.

```shell
ees_microsoft_outlook -c ~/config.yml full-sync
```

#### `bootstrap` command

Creates a Workplace Search content source with the given name. Outputs its ID.

```shell
ees_microsoft_outlook bootstrap --name 'Accounting documents' --user 'shay.banon'
```

See also [Create a Workplace Search content source](#create-a-workplace-search-content-source).

To use this command, you must [configure](#configure-the-connector) the following settings:

- [`enterprise_search.host_url`](#enterprise_searchhost_url-required)
- [`enterprise_search.api_key`](#enterprise_searchapi_key-required)

And you must provide on the command line any of the following arguments that are required:

- `--name` (required): The name of the Workplace Search content source to create.
- `--user` (optional): The username of the Elastic user who will own the content source. If provided, the connector will prompt for a password. If omitted, the connector will use the configured API key to create the content source.

#### `incremental-sync` command

Performs an [incremental sync](#incremental-sync) operation.

#### `full-sync` command

Performs a [full sync](#full-sync) operation.

#### `deletion-sync` command

Performs a [deletion sync](#deletion-sync) operation.

#### `permission-sync` command

Performs a [permission sync](#permission-sync) operation.

### Configuration settings

[Configure](#configure-the-connector) any of the following settings for a connector:

#### `connector_platform_type` (required)

The connector platform type.
Allowed values for connector_platform_type are `Microsoft Exchange` and `Office365`.

```yaml
connector_platform_type: 'Microsoft Exchange'
```
By default, it is set to `Office365`.

#### `microsoft_exchange.active_directory_server` (required for "Microsoft Exchange")

Microsoft Exchange active directory IP address or Hostname.

```yaml
microsoft_exchange.active_directory_server: 0.0.0.0
```

#### `microsoft_exchange.server` (required for "Microsoft Exchange")

Microsoft Exchange Server IP address or Hostname.

```yaml
microsoft_exchange.server: 0.0.0.0
```

#### `microsoft_exchange.username` (required for "Microsoft Exchange")

The username of the admin account for the Microsoft Exchange Server. See [Gather Microsoft Outlook details](#gather-microsoft-outlook-details).

```yaml
microsoft_exchange.username: 'bill.gates'
```

#### `microsoft_exchange.password` (required for "Microsoft Exchange")

The password of the admin account for the Microsoft Exchange Server. See [Gather Microsoft Outlook details](#gather-microsoft-outlook-details).

```yaml
microsoft_exchange.password: 'L,Ct%ddUvNTE5zk;GsDk^2w)(;,!aJ|Ip!?Oi'
```

#### `microsoft_exchange.domain` (required for "Microsoft Exchange")

The domain name for the Microsoft Exchange Server. See [Gather Microsoft Outlook details](#gather-microsoft-outlook-details).

```yaml
microsoft_exchange.domain: 'abc.xyz'
```

#### `microsoft_exchange.secure_connection` (required for "Microsoft Exchange")

Validate the SSL certificate if host is secured. Specify Yes if host is secured and want to validate the SSL certificate, else No. See [Gather Microsoft Outlook details](#gather-microsoft-outlook-details).

```yaml
microsoft_exchange.secure_connection: Yes
```
By default, it is set to Yes.

#### `microsoft_exchange.certificate_path` (required for "Microsoft Exchange")

The path of the SSL certificate to establish a secure connection with Microsoft Exchange server. See [Gather Microsoft Outlook details](#gather-microsoft-outlook-details).

```yaml
microsoft_exchange.certificate_path: 'C:/Users/banon/microsoft_outlook_1/certificate.cer'
```

#### `office365.client_id` (required for "Office365")

Client ID of Microsoft Azure application. See [Gather Microsoft Outlook details](#gather-microsoft-outlook-details).

```yaml
office365.client_id: 'a122dsad123334'
```

#### `office365.tenant_id` (required for "Office365")

Tenant ID of Microsoft Azure application. See [Gather Microsoft Outlook details](#gather-microsoft-outlook-details).

```yaml
office365.tenant_id: 'a122dsad123334a122dsad123334a122dsad123334'
```

#### `office365.client_secret` (required for "Office365")

Client Secret of Microsoft Azure application. See [Gather Microsoft Outlook details](#gather-microsoft-outlook-details).

```yaml
office365.client_secret: 'a122dsad123334a122dsad123334'
```

#### `enterprise_search.api_key` (required)

The Workplace Search API key. See [Create a Workplace Search API key](#create-a-workplace-search-api-key).

```yaml
enterprise_search.api_key: 'zvksftxrudcitxa7ris4328b'
```

#### `enterprise_search.source_id` (required)

The ID of the Workplace Search content source. See [Create a Workplace Search content source](#create-a-workplace-search-content-source).

```yaml
enterprise_search.source_id: '62461219647336183fc7652d'
```

#### `enterprise_search.host_url` (required)

The [Enterprise Search base URL](https://www.elastic.co/guide/en/enterprise-search/current/endpoints-ref.html#enterprise-search-base-url) for your Elastic deployment.
Note: To use Enterprise Search version 8 or above, port is required.

```yaml
enterprise_search.host_url: 'https://my-deployment.ent.europe-west1.gcp.cloud.es.io:9243'
```

#### `enable_document_permission`

Whether the connector should sync [document-level permissions (DLP)](#use-document-level-permissions-dlp) from Microsoft Outlook.
By default, it is set to Yes i.e. by default the connector will try to sync document-level permissions.

```yaml
enable_document_permission: Yes
```

#### `objects`

Specifies which Microsoft Outlook objects to sync to Enterprise Search, and for each object, which fields to include and exclude. When the include/exclude fields are empty, all fields are synced.

```yaml
objects:
  mails:
    include_fields:
    exclude_fields:
  calendar:
    include_fields:
    exclude_fields:
  tasks:
    include_fields:
    exclude_fields:
  contacts:
    include_fields:
    exclude_fields:
```

#### `start_time`

A UTC timestamp the connector uses to determine which objects to extract and sync from Microsoft Outlook. Determines the *starting* point for a [full sync](#full-sync).
Supports the following time format `YYYY-MM-DDTHH:MM:SSZ`
By default it is set to 180 days from current time.

```yaml
start_time: 2022-04-01T04:44:16Z
```

#### `end_time`

A UTC timestamp the connector uses to determine which objects to extract and sync from Microsoft Outlook. Determines the *stopping* point for a [full sync](#full-sync).
Supports the following time format `YYYY-MM-DDTHH:MM:SSZ`
By default it is set to current execution time.

```yaml
end_time: 2022-04-01T04:44:16Z
```

#### `log_level`

The level or severity that determines the threshold for [logging](#log-errors-and-exceptions) a message. One of the following values:

- `DEBUG`
- `INFO` (default)
- `WARNING`
- `ERROR`

```yaml
log_level: 'INFO'
```
By default, it is set to `INFO`.

#### `retry_count`

The number of retries to perform when there is a server error. The connector applies an exponential backoff algorithm to retries.

```yaml
retry_count: 3
```
By default, it is set to `3`.

#### `source_sync_sync_thread_count`

The number of threads the connector will run in parallel to fetch documents from the Microsoft Outlook. By default, the connector uses 5 threads.

```yaml
source_sync_sync_thread_count: 5
```

#### `enterprise_search_sync_thread_count`

The number of threads the connector will run in parallel for indexing documents to the Enterprise Search instance. By default, the connector uses 5 threads.

```yaml
enterprise_search_sync_thread_count: 5
```

For a Linux distribution with at least 2 GB RAM and 4 vCPUs, you can increase the thread counts if the overall CPU and RAM are under utilized, i.e. below 60-70%.

#### `connector.user_mapping`

The pathname of the CSV file containing the user identity mappings for [document-level permissions (DLP)](#use-document-level-permissions-dlp).

```yaml
connector.user_mapping: 'C:/Users/banon/microsoft_outlook_1/identity_mappings.csv'
```

#### Enterprise Search compatibility

The Microsoft Outlook connector package is compatible with Elastic deployments that meet the following criteria:

- Elastic Enterprise Search version greater than or equal to 7.13.0.
- An Elastic subscription that supports this feature. Refer to the Elastic subscriptions pages for [Elastic Cloud](https://www.elastic.co/subscriptions/cloud) and [self-managed](https://www.elastic.co/subscriptions) deployments.

#### Runtime dependencies

Each Microsoft Outlook connector requires a runtime environment that satisfies the following dependencies:

- Windows, MacOS, or Linux server. The connector has been tested with CentOS 7, MacOS Monterey v12.0.1, and Windows 10.
- Python version 3.6 or later.
- To extract content from images: Java version 7 or later, and [`tesseract` command](https://github.com/tesseract-ocr/tesseract) installed and added to `PATH`
- To schedule recurring syncs: a job scheduler, such as `cron`

## Connector Limitations

The following sections provide limitations of connector:

- The connector can't fetch files larger than 10 MB due to a limitation with the `exchange-lib` module. These files will not be indexed into Workplace Search.
- The `exchange-lib` module can be slow to return attachments from Mails, Calendars and Tasks. In some cases, attachments may be missing following an incremental sync. However, these missing attachments will be indexed in the next full-sync cycle.