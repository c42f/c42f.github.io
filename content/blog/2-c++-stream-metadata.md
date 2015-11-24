Title: Attaching metadata to C++ streams
Slug: c++-stream-metadata
Date: 2015-10-15
Summary: Attach arbitrary metadata to standard C++ streams
Status: draft


In C++, displaying `iostream` information when things go wrong can be a
pain.

```C++
void write_on_stream(std::ostream& out)
{
    out << "Write a thing";
    if (!out)
    {
        throw std::runtime_error(
            "Couldn't write to the stream.  "
            "No, I won't tell you which stream it was.  "
            "Don't give me that look, I don't know either."
        );
    }
}
```

It would be nice to be able to name the stream for logging when something goes
wrong.  At a first sight[^secondsight] the only way to do this seems to be to
put the stream in a wrapper object.  This works, but it feels a bit intrusive
and unnatural to me.  It also doesn't play well with third party libraries which
pass around standard library iostreams.

I just hit this problem again and realized the obscure `xalloc()`/`pword()`
custom formatting interface can be abused to solve it.  It's admittedly a bit of
a hack, but it works.  Let's say we want to attach the following metadata
struct:

```C++
struct StreamInfo
{
    std::string name; //< Name for the stream
    int64_t size;     //< Number of characters in stream, -1 if unknown

    StreamInfo(const std::string& name = "unknown_stream",
               int64_t size = -1)
        : name(name),
        size(size)
    { }
};
```

Inside each standard C++ stream there's a container for storing custom
formatting flags.  The `xalloc()` function allocates a new globally unique index
in this container.  You're meant to use it to control the formatting of custom
types[^xallocpurpose] but we're going to stash a `StreamInfo` in there.

```C++
const int g_streamInfoIndex = std::ios::xalloc();
```

Calling `stream.pword(g_streamInfoIndex)` now gives a reference to a `void*` on
the instance `stream`, and we can store anything we like there.  The
lifetime of heap objects assigned to a `pword` pointer need to be managed
carefully using the `register_callback` function.


```C++
/// Deallocate any attached StreamInfo on `erase_event`
static void deleteStreamInfo(std::ios_base::event event, std::ios_base& stream, int /*index*/)
{
    if (event != std::ios_base::erase_event)
        return;
    // erase_event => copyfmt() or ~ios_base() was called.  We'd like not to
    // delete the StreamInfo on a call to copyfmt(), but it's not really
    // possible to retain due to iostreams API assumptions.
    void*& ref = stream.pword(g_streamInfoIndex);
    if (ref)
    {
        delete static_cast<StreamInfo*>(ref);
        ref = 0;
    }
}


StreamInfo& getStreamInfo(std::ios_base& stream)
{
    void*& ref = stream.pword(g_streamInfoIndex);
    if (!ref)
    {
        ref = static_cast<void*>(new StreamInfo);
        stream.register_callback(deleteStreamInfo, 0);
    }
    return *static_cast<StreamInfo*>(ref);
}
```


```
void setStreamInfo(std::ios_base& stream,
                   const StreamInfo& info)
{
    getStreamInfo(stream) = info;
}

void setStreamInfo(std::ios_base& stream,
                   const std::string& name = "unknown_stream",
                   int64_t size = -1)
{
    setStreamInfo(stream, StreamInfo(name, size));
}


/// Set istringstream information, with sensible defaults
///
/// The size of the stream internal string buffer is assumed to be already filled by the time that setStreamInfo
///
/// calls to stream.str(newstring)
void setStreamInfo(std::istringstream& stream,
                   const std::string& name = "unknown_istringstream")
{
    setStreamInfo(stream, StreamInfo(name, true, stream.rdbuf()->in_avail()));
}

/// Set fstream information
void setStreamInfo(std::ifstream& stream,
                   const std::string& name = "unknown_ifstream")
{
    boost::system::error_code err;
    uint64_t fileSize = boost::filesystem::file_size(name, err);
    if (err) fileSize = -1;
    setStreamInfo(stream, StreamInfo(name, true, fileSize));
}


std::ostream& operator<<(std::ostream& out, const StreamInfo& info)
{
    out.setf(std::ios::boolalpha);
    out << "(name=\"" << info.name << "\", "
        << "size=" << info.size << ")";
    return out;
}


int main()
{
    std::istringstream iss("asdf");
    setStreamInfo(iss, "A string stream");

    {
        // Copyfmt must be 
        std::istringstream dummy;
        copyfmt(iss, dummy);
    }

    std::cout << getStreamInfo(iss) << "\n";

    const char* fileName = "/home/chris/dev/test/stream_info.cpp";
    std::ifstream file(fileName);
    setStreamInfo(file, fileName);
    std::cout << getStreamInfo(file) << "\n";

    return 0;
}
```

```C++
/// Unfortunately, basic_ios::copyfmt() will copy across the pwords list unconditionally, which means the 
template<typename C, typename T>
void copyfmt(std::basic_ios<C,T>& dest, std::basic_ios<C,T>& src)
{
    StreamInfo info = getStreamInfo(dest);
    dest.copyfmt(src);
    setStreamInfo(dest, info);
}
```



, or provide a way to clone the stream
for multithreaded processing instead of using locking

[^secondsight]: And to be honest, at least second, third, fourth, and fifth
sight...
[^xallocpurpose]: Imagine implementing the `std::boolalpha` manipulator if it
didn't already exist in the standard library - you'd need some way to attach the
flag to the stream, and a way to retrieve it inside `operator<<(std::ostream&, bool)`.

