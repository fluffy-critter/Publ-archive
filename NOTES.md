== Notes

===asset store

Keep the assets in the original named upload file hierarchy (static content or whatev).

Allow people to just add arbitrary assets within said hierarchy via scp/whatever.  reconcilation at process startup and maybe with specific user action

1. scan all files in database to ensure they exist. Return list of files which did not exist as map { sha => original_path }

2. scan all files in filesystem, computing SHA hash.
   * If item is in database, update SHA hash.
   * otherwise, if SHA matches one in step 1's map, change path in database
   * otherwise, create new file.

===image server
able to be hosted in separate domain. for CDNs etc

template engine will have format for getting an image from pathname/asset => generated name. this format will also generate (or queue for generation) the image to a static, readable store (public/img/ or configurable for CDN purposes or whatever). generated file should probably be just like `{source sha}_{width}.{extension}`

jinja formats should include
* generating an image URL for a specific resource, target width, and scale mode
* generating an image srcset declaration for the same

like maybe

    def image_src(asset, target_width, scale_mode="harmonic"):
        return generate_image(asset.path, actual_width)
    def image_srcset(asset, target_width, scale_mode, max_mult=3):
        specs=[]
        for each output size up to min(target_width*max_mult,width):
            specs.push("%s %dx" % generate_image(asset.path, actual_width))
        return specs.join(', ')
    # hey um how do we specify JPEG quality?

and then in template it looks like

    {% for chunk in page.chunks %}
        {img src="{{chunk.asset|image_src(500)}}" srcset="{{chunk.asset|image_srcset(500)}}

and then when run that'd be generating like

    <img src="/img/abc123_500.jpg" srcset="/img/abc123_500.jpg 1x, /img/abc123_1000.jpg 2x">


generate_image would also be all "hey that file already exists so i won't make it again". also its output should probably be memoized in the cache so it doesn't even need to check.