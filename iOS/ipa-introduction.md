# IPA File Format

> An IPA archive is the de facto way to package applications for iOS. The extension has no official definition, but is commonly called iPhone Application by the iOS community. The file is just a renamed ZIP archive. Although any computer with a ZIP archive reader can extract an IPA, PNG images (e.g. the app's icon files) are typically in a proprietary variant of the PNG format instead of the standardized PNG format, and the application binary is encrypted (DRM) which prevents examination of the binary.

## Contents

> As an IPA file is just a renamed ZIP archive, its structure is available from PKWARE.

- iTunesArtwork
- iTunesMetadata.plist
- Payload/
  - {ApplicationName}.app/
  - (various application files)

## Creation
> IPA files are typically created through Xcode, but may be created manually:

- Build application
- Locate the .app folder
- Create a folder named Payload
- Place your .app folder in it
- Create a 512x512 JPEG version of your icon (see above section)
- Save it as iTunesArtwork (no extension)
- Create your iTunesMetadata.plist and save it
- "ZIP" the contents
    - iTunesArtwork
    - iTunesMetadata.plist
    - Payload/