interface ConsentScreenProps {
  readonly onAccept: () => void;
}

export default function ConsentScreen({ onAccept }: ConsentScreenProps) {
  return (
    <div className="consent-screen">
      <div className="card consent-card">
        <p className="consent-eyebrow">Before you sign in</p>
        <h2>Review Data Access</h2>
        <p className="consent-intro">
          iCloud Photo Sorter needs your consent before it can use iCloud Photos metadata and your
          local iCloud Photos folder to organize files already synced to this computer.
        </p>

        <section className="consent-section" aria-labelledby="consent-metadata-heading">
          <h3 id="consent-metadata-heading">iCloud Photos metadata</h3>
          <p>
            The app reads metadata such as album names, asset filenames, and album membership so it
            can match selected albums to files on your PC.
          </p>
        </section>

        <section className="consent-section" aria-labelledby="consent-local-heading">
          <h3 id="consent-local-heading">Local folder access</h3>
          <p>
            The app accesses your local iCloud Photos folder to find matching files and move them
            into album folders during sorting.
          </p>
        </section>

        <section className="consent-section" aria-labelledby="consent-transfer-heading">
          <h3 id="consent-transfer-heading">Transfer boundaries</h3>
          <p>
            The app does not download images or videos from iCloud, and it does not upload files or
            data from your computer.
          </p>
        </section>

        <section className="consent-section" aria-labelledby="consent-credentials-heading">
          <h3 id="consent-credentials-heading">Apple ID credentials</h3>
          <p>
            Your Apple ID credentials are submitted to this app&apos;s local backend login flow and used
            only to sign in with Apple/iCloud through the app&apos;s iCloud authentication service. The
            app does not store your Apple ID password.
          </p>
        </section>

        <button type="button" onClick={onAccept}>
          I understand and agree
        </button>
      </div>
    </div>
  );
}
