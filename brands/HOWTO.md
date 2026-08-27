# Getting the logo into Home Assistant

Home Assistant does not read icons out of a custom integration. Everything the
UI shows — the tile under *Settings → Devices & Services*, the entry in the
add-integration dialog, the HACS listing — is fetched from
`https://brands.home-assistant.io/`, which is served from the
[home-assistant/brands](https://github.com/home-assistant/brands) repository.
There is no manifest field and no local override for this. Until the files are
merged there, Home Assistant draws its generic placeholder icon.

## The files

Ready to use, in `custom_integrations/cardwallet_deluxe/`:

| File | Size | Required |
| --- | --- | --- |
| `icon.png` | 256 × 256 | yes |
| `icon@2x.png` | 512 × 512 | optional |
| `logo.png` | 512 × 505 | optional |
| `logo@2x.png` | 1024 × 1010 | optional |

The icon is the emblem alone — the wordmark is unreadable below about 64 px,
which is the size Home Assistant actually draws it at.

The folder name must match `domain` in `manifest.json`, which is why it is
`cardwallet_deluxe` and not `cardwallet`. That also keeps it clear of the
upstream project, which owns the `cardwallet` domain.

## The pull request

```bash
git clone https://github.com/<user>/brands        # your fork of home-assistant/brands
cd brands
git checkout -b cardwallet-deluxe
mkdir -p custom_integrations/cardwallet_deluxe
cp /path/to/custom_integrations/cardwallet_deluxe/*.png custom_integrations/cardwallet_deluxe/
git add custom_integrations/cardwallet_deluxe
git commit -m "Add CardWallet Deluxe custom integration"
git push origin cardwallet-deluxe
```

Then open the pull request against `home-assistant/brands`. Their CI checks the
image dimensions and that the folder matches the integration's domain.
Reviewers do expect the repository behind a custom integration to be reachable
and installable via HACS.

## Meanwhile

The README shows the logo straight from `assets/logo.png`, so it is visible on
GitHub and in HACS's repository view right away — that part needs no pull
request.
