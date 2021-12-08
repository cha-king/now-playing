import { useEffect, useState } from 'react';

import Song from './Song.js';

function RecentlyPlayed() {
    const [songs, setSongs] = useState([]);

    useEffect(() => {
    async function getData() {
        const response = await fetch('/api/recently-played');
        const data = await response.json();

        const songs = data.map(obj => (
        <Song title={obj.name} artist={obj.artist} album={obj.album} imageUrl={obj.image_url}/>
        ));
        setSongs(songs);
    }
    getData();
    }, []);

    return songs;
}


export default RecentlyPlayed;
