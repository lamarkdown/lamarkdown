---
parent: Output Processing
---

# Resource Hashing

<!-- Resource hashing optionally applies to _non_-[embedded](embedding.md), external media, stylesheets and scripts.  -->

Lamarkdown can arrange for the output document to contain a hash (sha256, sha384 or sha512) for each of its external resources, so the browser can [verify their integrity](https://developer.mozilla.org/en-US/docs/Web/Security/Subresource_Integrity). This applies specifically to _non_-[embedded](embedding.md), external media, stylesheets and scripts.

Lamarkdown will use any defined `:hash` directive and `hash()` rule to compute an appropriate hash (or skip hashing) for each non-embedded resource. Where a hash is computed, it will appear as the value of the `integrity` HTML attribute in the output document.

{.note}
Hashing is not available for embedded resources. Any adversary able to modify an embedded resource in the output document could simply also modify the hash.

Hashing is a compromise between the control afforded by embedding, and the smaller file sizes offered by not embedding. Embedding may (depending on the particular files) significantly increase the file size of the output document. But with non-embedded, non-hashed resources, you must _trust_ the external source(s), because you are ceding control over aspects of the document. For instance, if your document links to `http://example.com/image.jpg`, then your document will show _whatever_ that image is at the time. If/when the image is replaced on the server, your document will show the new version, and for a reader, there won't be any sign that it's not the original. 

The same and worse could happen for stylesheets and scripts. An external entity with control over a stylesheet or script in your document could choose to disable or arbitrarily modify your entire document remotely, for anyone reading it. With embedded or hashed resources, these are no longer possibilities.

However, resource hashing lacks other advantages of embedded resources:

* Readers require an internet connection to view hashed resources, and must wait a moment for them to load, while embedded resources will be available offline and practically instantaneously.
* An external entity (controlling a hashed resource) might be able to track readers of the document, by recording requests for the document's external resource(s) and mapping them to readers' IP addresses.
* Hashing won't protect the document against its resources being moved or deleted.

There's also a chance that you may _want_ the external source to be able to change the resource arbitrarily. In this case, a non-embedded, non-hashed resource would be appropriate.

## The `:hash` output directive

## The `hash()` rule

TODO
