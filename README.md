# ugly-rss-reader
Hopefully not an ugly reader for RSS, but an RSS reader for ugly RSSes.

Especially meant for RSS feeds which are frequently updated or shuffled around. It can be fully controlled from the command line.

It tries to use the news link as key to determine if the news was already seen.

# Usage

`reader.py [options] <feed url>`

It will produce unread feed items (with title, summary, date of publication, link) on standard output.

# Command line options

  * `--days=<number>`

Ignores items older than the specified number of days.

  * `--1`

Prints one news item and exits.

  * `--dry-run`

Does not set the news as read.

  * `--debug`

Prints all available info about the news items.

# Dependencies

  * feedparser
  * sqlite3


