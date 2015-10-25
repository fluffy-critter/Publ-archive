# Notes

## asset store

Keep the assets in the original named upload file hierarchy (static content or whatev).

Allow people to just add arbitrary assets within said hierarchy via scp/whatever.  reconcilation at process startup and maybe with specific user action

1. scan all files in database to ensure they exist. Return list of files which did not exist as map { sha => original_path }

2. scan all files in filesystem, computing SHA hash.
   * If item is in database, update SHA hash.
   * otherwise, if SHA matches one in step 1's map, change path in database
   * otherwise, create new file.

## image server
able to be hosted in separate domain. for CDNs etc

template engine will have format for getting an image from pathname/asset => generated name. this format will also generate (or queue for generation) the image to a static, readable store (public/img/ or configurable for CDN purposes or whatever). generated file should probably be just like `{source sha}_{width}.{extension}`

jinja formats should include

* generating an image URL for a specific resource, target width, and scale mode
* generating an image srcset declaration for the same

like maybe

    def image_src(asset, target_width, scale_mode="harmonic"):
        return generate_image(asset.path, actual_width)
    def image_srcset(asset, target_width, scale_mode="harmonic", max_mult=3):
        specs=[]
        for each output size up to min(target_width*max_mult,width):
            specs.push("%s %dx" % generate_image(asset.path, actual_width))
        return ", ".join(specs)

and then in template it looks like

    {% for chunk in page.chunks %}
        {img src="{{chunk.asset|image_src(500)}}" srcset="{{chunk.asset|image_srcset(500)}}

and then when run that'd be generating like

    <img src="/img/abc123_500.jpg" srcset="/img/abc123_500.jpg 1x, /img/abc123_1000.jpg 2x, /img/abc123_1720.jpg 3x">

generate_image would also be all "hey that file already exists so i won't make it again". also its output should probably be memoized in the cache so it doesn't even need to check.


## sections

Example setup for beesbuzz.biz:

* /
    * art/
        * photo/
    * comics/
        * unity/
            * ascent/
            * distribution/
                * planetfall/
                * breeder/
        * lewi/
    * blog/

URL scheme could be something like:

    /admin/... (post, edit, reblog, etc.)
    /user/login
    /user/logout
    /user/profile/<username>
    /feed
    /s/<section>[/feed]
    /s/<section>/p/<pageid> -> /s/<section>/p/<pageid>/<seotext>
    /s/<section>/d/<date_str>[/feed] - example potential formats: Y-M-D, Y-M, Y-wW (week) [this logic can come later]
    /s/<section>/tagged/<tagspec>[/feed]
    /s/<section>/<static_title>
    /tagged/<tagspec>[/feed]

Examples of how this would work:

* `/s/comics/p/123` would redirect to `/s/comics/p/123/asdf`
* `/s/comics/p/123/asdf` would display page id 123, with prev/next links within the 'comics' section and using the 'comics' theme
* `/s/ascent/p/123/asdf` would display page id 123, with prev/next links within the 'ascent' section and using the 'ascent' theme
* Comic section templates could show the latest comic within this section (recursively) with nav links within that context, as well as some interface for choosing subsections
    * `/s/comics/` would show latest comic for all series (with nav links in that context), list of series, etc.
    * `/s/distribution/` would just show latest comic from 'distribution' with nav links there, the list of series within distribution

We probably want non-index templates as well, like maybe `/<section>/menu` to get a menu of subsections and so on

Internally this could just work by having a generic thing for filtering entries and, in the /feed case, maps to a generic atom template, and otherwise finds the Jinja template to map the data to. Even the `/p/<pageid>` templates would just provide the object as an `entries` query so we don't need to do anything special for the singleton case. (There would also be a `section` object provided, for navigating based on current/child/parent sections, and probably some CSS selection logic if we don't want to just make that part of the templates but we probably do.)

Each Jinja2 template probably gets the following objects:

* `section` - the section we're in
* `entries` - the filtered entries that match the current view spec
* `nav` - navigation links that relate to the current view (e.g. switching between data/entry/section-wise contexts, going to next/previous page in current context, etc.)

If someone requests `/s/section/p/page` for a page that's not in the section, then they'll get the wrong theme and nav context, but that requires a conscious effort on their part and doesn't actually break anything, so I see no reason to bother validating that.
