# Development container locales

The development image provides both `C.UTF-8` and `en_US.UTF-8`. Container and
VS Code remote processes default to `C.UTF-8`; the generated `en_US.UTF-8` locale
also supports tools that inherit that value from the host or editor.

After changing the Dockerfile or environment settings, run **Dev Containers:
Rebuild Container** in VS Code. Opening another terminal alone does not rebuild
the image or refresh an already running editor server.

To check the result:

```bash
locale -a
LC_ALL=en_US.UTF-8 bash -c 'locale charmap'
LC_ALL=C.UTF-8 bash -c 'locale charmap'
```

Both commands should print `UTF-8` without a `setlocale` warning.

A rejected Conventional Commit message is a separate issue. Use a message such
as `fix(ui): support quantity navigation on iPad`.
