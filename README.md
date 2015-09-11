# Publ

Yet another online publishing system.

Not a lot to see here. Also is being developed in tandem with [DreamCatcher](https://github.com/plaidfluff/dreamcatcher.git) so things are going to be wonky for a while.

High-level goals:

* Decentralized social aspects (allow OpenID/OAuth/URL tokens for login)
* Private entries with ACLs (managed like LJ friend groups or G+ circles)
* Single, flexible publishing engine for any sort of content (comics, photo sets, prose, blogs, etc.)
* Able to maintain separate sections with different themes/templates (incl. navigation schemata)
* All subscription functionality is via RSS/atom feeds (so people can use feed.ly, FeedOnFeeds, etc. as their "dashboard")
* CDN-friendly, HiDPI-capable image rendering/retrieval
* Easy deployment on shared hosting (at least where Passenger is supported, e.g. Dreamhost)
* Support for multiple authors, using ACLs to grant publish rights to various sections

Secondary goals:

* Nice integration with an RSS reader as a "dashboard"
* Support for [Webmention](http://indiewebcamp.com/webmention) and [PubSubHubbub](https://github.com/pubsubhubbub)
* Destroy all walled gardens while improving Internet privacy

See also [my manifesto on how the Internet should be](http://beesbuzz.biz/blog/e/2014/09/07-lets_build_a_social_network.php#manifesto).