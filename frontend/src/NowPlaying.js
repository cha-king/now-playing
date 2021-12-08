import { useState, useEffect } from 'react';

import Song from './Song.js';

function NowPlaying() {
    const [song, setSong] = useState(null);
    
    useEffect(() => {
        async function getNowPlaying() {
            const response = await fetch('/api/now-playing');
            if (response.status === 204) {
                setSong(null);
            }
            const data = await response.json();
            setSong(data);
        }
        getNowPlaying();
    }, []);

    if (song === null) {
        return <div>Nothing is currently playing</div>
    }
    
    return <Song title={song.name} artist={song.artist} album={song.album} imageUrl={song.image_url}/>
}

export default NowPlaying;
