Title: Symbol fonts for linux terminals
Slug: crisp-terminal-fonts
Date: 2015-12-29
Summary: Crisp unicode symbol fonts in a minimal terminal

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
setup was the real time waster of this whole exercise.  As it turned out the
ugliness was due to two problems

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
saved it to `.config/fontconfig/fonts.conf`.  Now, this was hacked together
until it worked by skim reading a bunch of web pages rather than involving any
real appreciation of the underlying system, so Caveat Emptor:
```xml
<?xml version="1.0"?>
<!DOCTYPE fontconfig SYSTEM "fonts.dtd">
<fontconfig>
  <!-- Try to get a better fallback for greek symbols for use with Terminus -->
  <alias>
    <family>Terminus</family>
    <prefer>
      <family>Liberation Mono</family>
      <family>Monospace</family>
    </prefer>
    <default><family>DejaVu Sans Mono</family></default>
  </alias>
</fontconfig>
```

I didn't find anything which was a perfect fit for Terminus, but Liberation Mono
is a lot less bad than `DejaVu Sans`.  The *fixed width* `DejaVu Sans Mono` is
actually pretty ok too.


### Hinting woes with `hintslight`

Even after all of the above, the symbol glyphs were still a blurry mess compared
to Terminus, and switching st entirely to Liberation Mono didn't make things
better.  Enter *hinting*, which modifies glyphs to fit crisply within the
constraints of a pixel grid.  I found that xubuntu 14.04 ships with a default
"hintslight" style in `/etc/fonts/conf.avail/10-hinting-slight.conf`, which
really doesn't do much to address overly blurry terminal fonts.  This seems
especially noticeable for light text on dark backgrounds.  Ok, we can hack that
in, here's the config:
```xml
<?xml version="1.0"?>
<!DOCTYPE fontconfig SYSTEM "fonts.dtd">
<fontconfig>
  <!-- Try to get a better fallback for greek symbols for use with Terminus -->
  <alias>
    <family>Terminus</family>
    <prefer>
      <family>Liberation Mono</family>
      <family>Monospace</family>
    </prefer>
    <default><family>DejaVu Sans Mono</family></default>
  </alias>
  <!-- Use reasonable hinting.  Full hinting with hintfull really helps get
  crisp fonts in the terminal, but it's a bit stark for use on the web. -->
  <match target="font">
    <edit name="hintstyle" mode="assign"><const>hintmedium</const></edit>
  </match>
</fontconfig>
```

![Relatively crisp symbols]({attach}crisp_symbols.png)

Now, this is still far from pretty, mainly due to the clash between the vertical
compactness of Terminus with the relatively larger Liberation Mono.  However, it
may have to be good enough unless I want to give up Terminus entirely.  In that
case having hinting turned up a bit really saves the day by avoiding a blurry
mess for all the usual latin glyphs which make up the bulk of text I'm likely to
read in a terminal.


## How many symbols are too many symbols?

So, now that I have beautiful crisp font rendering in my terminal emulator,
it's ever so tempting to start using them all over the place.  Under the
principle that code is more often read than written, it seems to make sense to
use symbols to the extent that they aid readability.  This can be the case in
mathematical code where a strong convention exists - using the conventional
symbol conveys a lot of meaning in small space.  It can also help when
transcribing existing notation into code, and it looks great in comments.

Having said all that, I'm trying to restrain myself from going too symbol
crazy.  The main problem is that symbols are harder to type (depending heavily
on your text editor, keyboard setup, etc), and may be basically impossible for
many users.  For people using non-unicode capable terminals such as xterm, they
may even be impossible to see!  For this reason I think it's best to avoid
using symbols in any public API, at least not without providing a well named
ascii alternative.

![Too many symbols?]({attach}julia_unicode_session.png)
