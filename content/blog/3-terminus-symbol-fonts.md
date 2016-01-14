Title: Symbol fonts for linux terminals
Slug: crisp-terminal-fonts
Date: 2015-12-29
Summary: Crisp unicode symbol fonts in a minimal terminal
Modified: 2016-01-13

The [julia language](http://julialang.org/) supports UTF-8 encoding by default,
and this can be used to make code look a lot more like mathematical notation.
Lately I'm finding this very nice for prototyping, and particularly for simple
mathematical notation in code comments.  Unfortunately getting symbol fonts
which look usably crisp at medium to small font sizes is not entirely simple: it
requires modifying the fontconfig setup, and finally ditching xterm for
something which can deal properly with unicode.

I've used the Terminus bitmap font for years and it's left me with a taste for
very crisp terminal fonts.  In a bitmap font, the glyphs are designed at a given
size so that pixels are either on or off.  A well designed font like Terminus is
about the sharpest thing you can hope for in a terminal, but comes without any
scalability, and without glyphs for the unicode math symbols I'm suddenly
wanting.


## Goodbye xterm

xterm is a crufty old thing and has no hope when it comes to displaying symbols
because it really doesn't support unicode at all.  A reasonable replacement is
`urxvt`, but I went with [st](http://st.suckless.org/) instead because it's
tastefully minimal.  `st` is configured by editing the source `config.h` and
various tweaks including adding Terminus as the font were quite easy.  I put my
personal changes - including adding the scrollback buffer patches from the
suckless wiki - [up on github](https://github.com/c42f/st).  (Subject to change
at random whim, you've been warned ;-) )


## Tweaking fontconfig

Even after setting up st, the symbol glyphs still looked awful, particularly ϕ
which overflowed its box into the neighbouring glyph:

![Blurry default symbol fonts]({attach}default_blurry_symbols.png)

The resulting dive into the fontconfig font fallback system and font hinting
setup was the real time waster of the whole exercise.  As it turned out the
ugliness was due to three problems:

### Terminus doesn't have symbol glyphs

When a font doesn't have required glyphs, fontconfig gets them from a computed
fallback font.  In this case the fallback turned out to be DejaVu Sans which
combines pretty terribly, given that Terminus is very compact and DejaVu Sans
isn't even fixed width!

I found a
[useful and amusing blog post](http://eev.ee/blog/2015/05/20/i-stared-into-the-fontconfig-and-the-fontconfig-stared-back-at-me)
by Eevee, recording some of the weird things fontconfig does when the font
matching rules don't do what you expect.  Included are some useful debugging
tips: To see the fallback list which will be considered, you need something like
`fc-match -s Terminus`.  To see the actual font which would be used for a given
character (μ say) you can use
```bash
DISPLAY=:0 FC_DEBUG=4 pango-view --font=terminus -t μ | grep family:
```

To fix the Terminus fallback, I hacked together a fontconfig conf file, and
saved it to `$HOME/.config/fontconfig/fonts.conf`.  Now, this was hacked
together until it worked rather than involving any real appreciation of the
underlying system, so Caveat Emptor:
```xml
<?xml version="1.0"?>
<!DOCTYPE fontconfig SYSTEM "fonts.dtd">
<fontconfig>
  <!-- Try to get a better fallback for greek symbols for use with Terminus -->
  <alias>
    <family>Terminus</family>
    <prefer>
      <family>Cousine</family>
      <family>Liberation Mono</family>
      <family>Monospace</family>
    </prefer>
    <default><family>DejaVu Sans Mono</family></default>
  </alias>
</fontconfig>
```

I didn't find anything which was a perfect fit for Terminus, but the fixed width
font `Cousine` from the Chrome OS core font set is a reasonable fit.  It's also
got excellent coverage of the unicode mathematical symbols, much better than
most of the other fonts I played with.  This turns out to be important for
rendering the [greek phi](http://graphemica.com/%CF%95) in particular (UTF-8
encoding `0xCF 0x95`).  I got lost here for a while by using `Liberation Mono`
as a fallback which has most greek characters, but lacks the mathematical phi
glyph, resulting in ongoing ugliness.  Other than that, `Liberation Mono` is a
reasonable fallback, and the *fixed width* `DejaVu Sans Mono` is actually pretty
ok too.  Any of these are a far better match than the variable width `DejaVu
Sans` which fontconfig seems to choose by default.

In any case, the Cousine fallback is quite reasonable, and I probably would have
stopped there if not for the confusion with the missing `Liberation Mono` glyphs:

![Cousine fallback]({attach}cousine_fallback.png)


### Hinting woes with `hintslight`

Even after all of the above, the symbol glyphs are still relatively blurry
compared to Terminus, and switching st entirely to Cousine didn't make things
better.  Enter *hinting*, which modifies glyphs to fit crisply within the
constraints of a pixel grid.  I found that xubuntu 14.04 ships with a default
"hintslight" style in `/etc/fonts/conf.avail/10-hinting-slight.conf`, which
looks nice in black-on-white colour schemes (eg, a web browser) but really
doesn't do much to address overly blurry terminal fonts.  Ok, we can hack that
in by adding an extra block to the config file:
```xml
  <match target="font">
    <edit name="hintstyle" mode="assign"><const>hintfull</const></edit>
  </match>
```

![Relatively crisp symbols]({attach}crisp_symbols.png)

In this sample, it's not clear this is making a real improvement, but the
difference is more positive with a wider range of glyphs (for example, if I were
to ditch Terminus entirely).  Unfortunately, I found this setting a bit stark
for use in a web browser and other black-on-white colour schemes.  A hacky
workaround is to restrict full hinting to only apply to Cousine, which works if
it's not the default font in other applications:
```xml
  <match target="font">
    <test name="family"> <string>Cousine</string> </test>
    <edit name="hintstyle" mode="assign"><const>hintfull</const></edit>
  </match>
```

Part of the reason this isn't a huge improvement is that the antialiasing of
symbols is still greyscale.  On LCD monitors, each pixel is made up of
RGB subpixels which are spatially separated.  Making use of this gives extra
spatial resolution in the antialiased result.  To turn on subpixel antialiasing,
the system needs to know the spatial arrangement of subpixels (RGB
left-to-right, top-to-bottom, etc).  You can figure this out with a [specially
designed raster](http://www.lagom.nl/lcd-test/subpixel.php).  My particular
system is the most common RGB left-to-right, so adding the following block to
the config file should do the trick:
```xml
  <match target="font">
    <edit name="rgba" mode="assign"> <const>rgb</const> </edit>
  </match>
```
... or not.  Forgetting Terminus for the moment, the above snippet does work
fine if you ditch Terminus in st and use Cousine directly as the primary font:

![Working subpixel hinting]({attach}cousine_subpixel.png)

(Keep in mind that this image will only look good on your screen if (a) your
subpixel layout is the same as mine, and (b) you view it at a scale of 1:1 pixel
for pixel.)  The strange subpixel result brings us to the third problem.


### Subpixel hinting bugs

st, fontconfig or something else seems confused when using subpixel rendering
and a mix of bitmap font (Terminus) and antialiased fallback font (Cousine).
The result is that some glyphs are subpixel antialiased and some not, apparently
at random.  As a further complication, even enabling subpixel antialiasing
causes st to run extremely slowly when rendering a lot of symbols; clearly
something odd is going on.  To be quite honest, I haven't figured out how to fix
this yet, but it probably involves hacking the st source.


## Aside: How many symbols are too many symbols?

So, now that I have relatively crisp font rendering in my terminal emulator,
it's ever so tempting to start using symbols all over the place.  Under the
principle that code is more often read than written, it seems to make sense to
use symbols to the extent that they aid readability.  This can be the case in
mathematical code where using the conventional symbol conveys a lot of meaning
in a small space.  It can also help when transcribing existing notation into
code, and it looks great in comments.

Having said all that, I'm trying to restrain myself from going too symbol
crazy.  The main problem is that symbols are harder to type (depending heavily
on your text editor, keyboard setup, etc), and may be basically impossible for
many users.  For people using non-unicode capable terminals such as xterm, they
may even be impossible to see!  For this reason I think it's best to avoid
using symbols in any public API, at least not without providing a well named
ascii alternative.

![Too many symbols?]({attach}julia_unicode_session.png)
