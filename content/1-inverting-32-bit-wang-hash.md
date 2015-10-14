Title: Inverting Thomas Wang's 32 bit integer hash
Slug: inverting-32-bit-wang-hash
Date: 2015-09-21
Summary: Bit twiddling entertainment

A collegue at work recently asked for the inverse of the
[2002 version](http://web.archive.org/web/20060507103516/http://www.cris.com/~Ttwang/tech/inthash.htm)[^versionnote]
of Thomas Wang's 32 bit mix function.  Here is a C++ implementation:

```C++
uint32_t inthash(uint32_t key)
{
    key += ~(key << 15);
    key ^= (key >> 10);
    key += (key << 3);
    key ^= (key >> 6);
    key += ~(key << 11);
    key ^= (key >> 16);
    return key;
}
```

This is an invertible hash which also does a good job of mixing the bits -
changing a bit in the input leads to changing many bits in the output.
It shows up in various places on the web, for example in the
[chromium source](https://chromium.googlesource.com/chromium/blink/+/master/Source/wtf/HashFunctions.h).

Geoffrey Irving has worked out the
[inverse for the 64 bit version](https://naml.us/blog/2012/03/inverse-of-a-hash-function),
but a quick search didn't show up a solution for the 32 bit version.  This
seemed like a [cute problem](https://xkcd.com/356), so rather than look around
on the web I spent a few fun hours fiddling and came up with something.

----

To make the data flow clearer, I think it helps to change notation to name all
the states in the computation and avoid mutating `key`:

```C++
uint32_t hash(uint32_t key)
{
    uint32_t k0 = key;
    uint32_t k1 = k0 + ~(k0 << 15);
    uint32_t k2 = k1 ^  (k1 >> 10);
    uint32_t k3 = k2 +  (k2 <<  3);
    uint32_t k4 = k3 ^  (k3 >>  6);
    uint32_t k5 = k4 + ~(k4 << 11);
    uint32_t k6 = k5 ^  (k5 >> 16);
    return k6;
}
```

There's basically two types of steps here:

  1. Steps involving arithmetic operations and left shifts, possibly with a
     bitwise negation.
  2. Steps involving bitwise xor and right shifts


All steps of the first type can be rewritten as combinations of multiplication
and a bitwise negation.  For example (in mod 32 arithmetic):

```C++
k1 = k0 + ~(k0 << 15)
   = k0 - (k0<<15) - 1    // since  ~u + u + 1 = 0  for any u
   = k0 - (1<<15)*k0 - 1
   = -((1<<15) - 1)*k0 - 1
   = ~(((1<<15) - 1) * k0)
```

Now, $2^{15} - 1$ is relatively prime to $2^{32}$, so there exists a $\mod 2^{32}$
[modular multiplicative inverse](https://en.wikipedia.org/wiki/Modular_multiplicative_inverse).
Obviously bitwise negation `~` is also invertible, so these types of steps are
invertible.  The [julia](http://julialang.org) language provides a handy
implementation of the multiplicative inverse:

```julia
julia> invmod(2^15-1, 2^32)
3221192703
```

so we have `k0 = 3221192703*~k1`.  Inverses of the other steps of this type
can be readily calculated in a similar way.


Steps of the second type are Feistel functions, as [noted in the blog post about
the 64 bit version](https://naml.us/blog/2012/03/inverse-of-a-hash-function), so
they're also invertible.

The simplest example is `k6`: decompose `k5` and `k6` into low and high 16 bit
parts:

```C++
k5 = (k5High<<16) + k5Low
k6 = (k6High<<16) + k6Low
```

then `k6 = k5^(k5>>16)` is just

```
k6High = k5High
k6Low = k5Low ^ k6High   // ^ is xor here!
```
thus
```
k5High = k6High
k5Low = k6Low ^ k6High   // a = b^c  <=>  a^c = b
```

so `k5->k6` is its own self-inverse which is neat.  The others of this
type could be done iteratively using something like the above.  The
smaller the shift amount, the more iterations required to compute
the full inverse.

A neat alternative way to look at these operations is as matrix multiplication
where the `uint32` values are thought of vectors of 32 bits.  As bits, the
matrices and vectors are constructed from elements of the
[field GF(2)](https://en.wikipedia.org/wiki/GF%282%29) where mutliplication is
logical `and`, and addition is logical `xor`.  This helps if you want to see how
to construct a non-iterative inverse.

Here's a julia session using the
[IntModN](https://github.com/andrewcooke/IntModN.jl) package which makes it easy to work
with GF(2), in particular inverting the matrix just uses the standard machinery
(matlab, eat ya heart out!)


```julia
julia> using IntModN
julia> const wordsize = 16
julia> make_matrix(n) = map(GF2, eye(Int, wordsize) +
                        diagm(ones(Int, wordsize-abs(n)), -n))

# Matrix representing k4 = k3 ^ (k3 >> 6)
# In 16 bit arithmetic to keep matrix size managable:
julia> make_matrix(6)
16x16 Array{IntModN.ZField{2,Int64},2}:
 1  0  0  0  0  0  0  0  0  0  0  0  0  0  0  0
 0  1  0  0  0  0  0  0  0  0  0  0  0  0  0  0
 0  0  1  0  0  0  0  0  0  0  0  0  0  0  0  0
 0  0  0  1  0  0  0  0  0  0  0  0  0  0  0  0
 0  0  0  0  1  0  0  0  0  0  0  0  0  0  0  0
 0  0  0  0  0  1  0  0  0  0  0  0  0  0  0  0
 1  0  0  0  0  0  1  0  0  0  0  0  0  0  0  0
 0  1  0  0  0  0  0  1  0  0  0  0  0  0  0  0
 0  0  1  0  0  0  0  0  1  0  0  0  0  0  0  0
 0  0  0  1  0  0  0  0  0  1  0  0  0  0  0  0
 0  0  0  0  1  0  0  0  0  0  1  0  0  0  0  0
 0  0  0  0  0  1  0  0  0  0  0  1  0  0  0  0
 0  0  0  0  0  0  1  0  0  0  0  0  1  0  0  0
 0  0  0  0  0  0  0  1  0  0  0  0  0  1  0  0
 0  0  0  0  0  0  0  0  1  0  0  0  0  0  1  0
 0  0  0  0  0  0  0  0  0  1  0  0  0  0  0  1

# Now the inverse
julia> inv(make_matrix(6))
16x16 Array{IntModN.ZField{2,Int64},2}:
 1  0  0  0  0  0  0  0  0  0  0  0  0  0  0  0
 0  1  0  0  0  0  0  0  0  0  0  0  0  0  0  0
 0  0  1  0  0  0  0  0  0  0  0  0  0  0  0  0
 0  0  0  1  0  0  0  0  0  0  0  0  0  0  0  0
 0  0  0  0  1  0  0  0  0  0  0  0  0  0  0  0
 0  0  0  0  0  1  0  0  0  0  0  0  0  0  0  0
 1  0  0  0  0  0  1  0  0  0  0  0  0  0  0  0
 0  1  0  0  0  0  0  1  0  0  0  0  0  0  0  0
 0  0  1  0  0  0  0  0  1  0  0  0  0  0  0  0
 0  0  0  1  0  0  0  0  0  1  0  0  0  0  0  0
 0  0  0  0  1  0  0  0  0  0  1  0  0  0  0  0
 0  0  0  0  0  1  0  0  0  0  0  1  0  0  0  0
 1  0  0  0  0  0  1  0  0  0  0  0  1  0  0  0
 0  1  0  0  0  0  0  1  0  0  0  0  0  1  0  0
 0  0  1  0  0  0  0  0  1  0  0  0  0  0  1  0
 0  0  0  1  0  0  0  0  0  1  0  0  0  0  0  1
```

Each band of the inverse can be implemented with a bitshift.  In 16 bit
arithmetic, this is `k3 = k4 ^ (k4<<6) ^ (k4<<12)`.  For the 32 bit case, we
have:
```C++
uint32_t k3 = k4 ^ (k4 >> 6) ^ (k4 >> 12) ^ (k4 >> 18) ^ (k4 >> 24) ^ (k4 >> 30);
```


Blah blah theory theory whatever just show the solution.  Ok, here's C++ code for the inverse:


```C++
uint32_t unhash(uint32_t hashval)
{
    uint32_t k6 = hashval;
    uint32_t k5 = k6 ^ (k6 >> 16);
    uint32_t k4 = 4290770943 * ~k5;
    uint32_t k3 = k4 ^ (k4 >> 6) ^ (k4 >> 12) ^ (k4 >> 18) ^ (k4 >> 24) ^ (k4 >> 30);
    uint32_t k2 = 954437177 * k3;
    uint32_t k1 = k2 ^ (k2 >> 10) ^ (k2 >> 20) ^ (k2 >> 30);
    uint32_t k0 = 3221192703 * ~k1;
    return k0;
}
```

Here's a [complete test program]({attach}wang_hash_inverse.cpp) which exhaustively
checks that `unhash(hash(i)) == i` for all $2^{32}$ possible values.


[^versionnote]: There's more than one version of this hash, but I didn't realise
it to start with.  According to the Internet Archive, the version used here is
from 2002, but there's also more recent (presumably improved)
[2006 version](http://web.archive.org/web/20090408063205/http://www.cris.com/~ttwang/tech/inthash.htm).
