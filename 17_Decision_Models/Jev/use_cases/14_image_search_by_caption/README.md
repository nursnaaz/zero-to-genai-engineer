# 14 Search your images by what is in them

**Intermediate** | shapes used: `noul per image`

Search a photo library by content rather than filename, using one short caption per image.

## Run it

```bash
cd 14_image_search_by_caption
python3 search_images.py
```

## Data

`data/images.json` - 15 images with one-line captions.

## How it is tested

4 queries with expected result sets; reports precision and recall per query and asserts mean recall >= 0.6.

## Result when I ran it

Mean precision 0.94, mean recall 1.00 across 4 queries.

## Worth knowing

If you have no captions, a cheap vision model writes them once; after that every search is Jev-only.

← [all use cases](../README.md)
