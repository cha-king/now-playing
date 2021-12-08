import { useState, useEffect } from 'react';

import styles from './NowPlaying.module.css';

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
        return null
    }
    
    // return (<Song title={song.name} artist={song.artist} album={song.album} imageUrl={song.image_url}/>)
    return (
        <div className={styles['now-playing']}>
            <img src={song.image_url} alt={song.album}/>
            <ul>
                <li className={styles['song-name']}>{song.name}</li>
                <li className={styles['album-name']}>{song.album}</li>
                <li className={styles['artist-name']}>{song.artist}</li>
            </ul>
        </div>
    )
}

export default NowPlaying;
