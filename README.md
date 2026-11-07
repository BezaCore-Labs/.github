# .github

The BezaCore Labs organization's GitHub profile.

`profile/README.md` is what GitHub shows on the organization's overview page. It
only shows once this repository is public.

## The images

Everything in `profile/assets/` with words or the brand's geometry in it is
built by `profile/assets/build.py`, from BezaCore Labs' brand sources: the three
typefaces, set as outlines because GitHub never loads web fonts into an image,
and the logo masters, embedded whole and unchanged. Every colour is a brand
token. Each heading, icon and graphic has a dark and a light version, and the
profile shows the one that matches the reader's GitHub theme.

```bash
python profile/assets/build.py --brand <path to the brand directory>
```

It needs `fontTools`. `--still` builds every image without motion. The rings
in the banner and the graphic draw in once and then stay still, and they don't
move at all for a reader who has asked for reduced motion.

The profile links its images by their full `raw.githubusercontent.com` address,
because it is shown on the organization's page rather than in this repository,
where a relative path has nothing to resolve against. So a changed image shows
on the profile only once it is on `main`, and none of them load while the
repository is private.

The four icons are [Lucide](https://lucide.dev)'s, under the ISC licence. The
badges come from [shields.io](https://shields.io) and the stack icons from
[skillicons.dev](https://skillicons.dev).
