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
      console.error('station-fietsen-data element niet gevonden');
      stationFietsen = {};
    } else {
      console.log('Ruwe station-fietsen-data:', dataElement.textContent); // Debug
      stationFietsen = JSON.parse(dataElement.textContent);
      console.log('Station fietsen:', stationFietsen);
      console.log('Station fietsen sleutels:', Object.keys(stationFietsen));
    }
  } catch (e) {
    console.error('Fout bij parsen van stationFietsen:', e);
    stationFietsen = {};
  }

  // Controleer DOM-elementen
  if (!popup || !popupStationName || !fietsCheckboxes || !fromStationIdInput || !closePopupButton) {
    console.error('DOM-elementen niet gevonden:', {
      popup, popupStationName, fietsCheckboxes, fromStationIdInput, closePopupButton
    });
    return;
  }

  openPopupButtons.forEach(button => {
    console.log('Knop station ID:', button.dataset.stationId); // Debug
    button.addEventListener('click', () => {
      const stationId = button.dataset.stationId;
      const stationCard = button.closest('.station-card');
      const stationName = stationCard ? stationCard.querySelector('.station-card-header').textContent : 'Onbekend';
      const fietsen = stationFietsen[stationId] || [];

      console.log('Open popup voor station:', { stationId, stationName, fietsen });

      // Vul popup
      popupStationName.textContent = stationName;
      fromStationIdInput.value = stationId;
      fietsCheckboxes.innerHTML = fietsen.length > 0
        ? fietsen.map(fiets => `
            <label>
              <input type="checkbox" name="fiets_ids" value="${fiets.id}">
              Fiets ID: ${fiets.id} (Status: ${fiets.status || 'Onbekend'})
            </label>
          `).join('')
        : '<p>Geen beschikbare fietsen op dit station.</p>';

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