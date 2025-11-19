# OpenTariff
Open source energy tariff definitions


Install with `pip install open-tariff`


## Creating a new release
New releases are now published to PyPi using the `.github\workflows\publish.yml` process. To create a new release do the following.

1. ### Checkout main branch
`git pull origin`
`git checkout main`

2. ### Check release history
`git tag -n`

3. ### Create a version tag
Depending on the changes add a new version number at the appropriate level. See here for guidance https://semver.org/
`git tag -a v1.0.0 -m "Some notes on what's included"`

4. ### Push the tag to GitHub to trigger the workflow
`git push origin v1.0.0`
