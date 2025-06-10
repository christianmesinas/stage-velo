// Mock _() functie voor pybabel extractie
function _(str) { return str; }

document.addEventListener('DOMContentLoaded', () => {
  const popup = document.getElementById('fiets-popup');
  const popupStationName = document.getElementById('popup-station-name');
  const fietsCheckboxes = document.getElementById('fiets-checkboxes');
  const fromStationIdInput = document.getElementById('from_station_id');
  const openPopupButtons = document.querySelectorAll('.open-popup');
  const closePopupButton = document.querySelector('.close-popup');

  // Haal fietsgegevens veilig op
  let stationFietsen;
  try {
    const dataElement = document.getElementById('station-fietsen-data');
    if (!dataElement) {
      console.error(_('station-fietsen-data element niet gevonden'));
      stationFietsen = {};
    } else {
      console.log(_('Ruwe station-fietsen-data:'), dataElement.textContent); // Debug
      stationFietsen = JSON.parse(dataElement.textContent);
      console.log(_('Station fietsen:'), stationFietsen);
      console.log(_('Station fietsen sleutels:'), Object.keys(stationFietsen));
    }
  } catch (e) {
    console.error(_('Fout bij parsen van stationFietsen:'), e);
    stationFietsen = {};
  }

  // Controleer DOM-elementen
  if (!popup || !popupStationName || !fietsCheckboxes || !fromStationIdInput || !closePopupButton) {
    console.error(_('DOM-elementen niet gevonden:'), {
      popup, popupStationName, fietsCheckboxes, fromStationIdInput, closePopupButton
    });
    return;
  }

  openPopupButtons.forEach(button => {
    console.log(_('Knop station ID:'), button.dataset.stationId); // Debug
    button.addEventListener('click', () => {
      const stationId = button.dataset.stationId;
      const stationCard = button.closest('.station-card');
      let stationName = button.dataset.stationName || _('Onbekend');
      // Fallback: haal naam uit tabelrij als data-station-name leeg is
      if (stationName === _('Onbekend')) {
        const stationRow = button.closest('tr');
        stationName = stationRow ? stationRow.cells[0].textContent : _('Onbekend');
      }
      const fietsen = stationFietsen[stationId] || [];

  console.log(_('Open popup voor station:'), { stationId, stationName, fietsen });
      console.log(_('Stationnaam ingesteld op:'), stationName); // Extra debug

      // Vul popup
      popupStationName.textContent = stationName;
      fromStationIdInput.value = stationId;
      fietsCheckboxes.innerHTML = fietsen.length > 0
        ? fietsen.map(fiets => `
            <label>
              <input type="checkbox" name="fiets_ids" value="${fiets.id}">
              ${_('Fiets ID')}: ${fiets.id} (${_('Status')}: ${fiets.status || _('Onbekend')})
            </label>
          `).join('')
        : `<p>${_('Geen beschikbare fietsen op dit station.')}</p>`;

      popup.style.display = 'flex';
    });
  });

  closePopupButton.addEventListener('click', () => {
    popup.style.display = 'none';
  });

  popup.addEventListener('click', (e) => {
    if (e.target === popup) {
      popup.style.display = 'none';
    }
  });
});
