## Description of Change
<!-- Provide a clear summary of what this change accomplishes and why it is needed. -->

## Related Issues
<!-- Link any related issues or feature requests (e.g. Closes #12). -->

## Type of Change
- [ ] Bug fix (non-breaking fix for an existing issue)
- [ ] New feature (non-breaking pedagogical, safety, or adapter enhancement)
- [ ] Performance optimization / Refactoring
- [ ] Documentation update
- [ ] Security / Safety gate enhancement

## Child Safety and Privacy Impact
- [ ] This change enforces fail-closed behavior on safety checks.
- [ ] This change does NOT leak PII, student emails, or unhashed IP addresses into logs or API responses.
- [ ] This change enforces tenant isolation and server-derived student identity.
- [ ] No changes were made that bypass guardian consent workflows.

## Tests Performed
<!-- Describe the automated and manual tests executed to verify your change. -->
- [ ] All backend unit tests pass: `python -m unittest discover -s backend/tests`
- [ ] Frontend build succeeds: `cd frontend && npm run build`

## Third-Party Code and Dependencies
- [ ] All code submitted is my original work, OR any third-party materials are clearly identified with upstream license attributions.

## Contributor License Agreement Confirmation
- [ ] **I have read and agree to the [Edufeedia Contributor License Agreement (CLA.md)](CLA.md).**
